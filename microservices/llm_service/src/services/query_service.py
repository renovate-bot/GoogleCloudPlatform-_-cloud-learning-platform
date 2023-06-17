# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" Query Engine Service """

import functools
import gc
import json
import tempfile
import time
import os
from typing import List, Optional, Generator, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from pathlib import Path
from common.utils.logging_handler import Logger
from common.models import (UserQuery, QueryResult,
                          QueryEngine, QueryDocument,
                          QueryDocumentChunk)
from common.utils.errors import ResourceNotFoundException
from common.utils.http_exceptions import InternalServerError
from common.utils import gcs_adapter
from google.cloud import aiplatform
from google.cloud import storage
from vertexai.preview.language_models import TextEmbeddingModel
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import CSVLoader
from langchain.chains import RetrievalQAWithSourcesChain
from PyPDF2 import PdfReader
import langchain_service

from config import PROJECT_ID

# text chunk size for embedding data
CHUNK_SIZE = 1000

# Create a rate limit of 300 requests per minute.
API_CALLS_PER_SECOND = 300 / 60

# According to the docs, each request can process 5 instances per request
ITEMS_PER_REQUEST = 5

# embedding dimensions generated by TextEmbeddingModel
DIMENSIONS = 768

async def query_generate(
            prompt: str,
            query_engine: str,
            user_query: Optional[UserQuery] = None) -> QueryResult:
  """
  Use langchain to execute a query over a query engine

  Args:
    prompt: the text prompt to pass to the query engine

    query_engine: the name of the query engine to use

    user_query (optional): an existing user query for context

  Returns:
    QueryResult: the query result object
  """
  q_engine = QueryEngine.find_by_name(query_engine)
  if q_engine is None:
    raise ResourceNotFoundException(f"cant find query engine {query_engine}")

  llm = langchain_service.get_model(q_engine.llm_type)
  docsearch = None
  chain = RetrievalQAWithSourcesChain.from_chain_type(llm, chain_type="stuff",
              retriever=docsearch.as_retriever())
  query_config = {"question": prompt}

  if user_query is not None:
    query_config.update({"context": user_query.history})

  chain_result = chain(query_config, return_only_outputs=True)
  query_result = QueryResult(query_engine_id=q_engine.id,
                             query_engine=query_engine,
                             results=[chain_result])

  return query_result

def query_engine_build(doc_url: str, query_engine: str,
                       params: Dict) -> QueryEngine:
  """
  Build a new query engine.

  Args:
    doc_url: the URL to the set of documents to be indexed

    query_engine: the name of the query engine to create

    params: query engine params

  Returns:
    QueryEngine: the query engine object
  """
  # create model
  is_public = params.get("is_public", True)
  user_id = params.get("user_id")
  query_engine = QueryEngine(name=query_engine,
                             created_by=user_id, is_public=is_public)
  query_engine.save()

  # build document index
  build_doc_index(doc_url, query_engine)

  return query_engine


def build_doc_index(doc_url:str, query_engine: str):
  """
  Build the document index.
  Supports only GCS URLs initially, containing PDF and CSV files.

  Args:
    doc_url: URL pointing to folder of documents
    query_engine: the query engine to

  Returns:
    None
  """
  q_engine = QueryEngine.find_by_name(query_engine)
  if q_engine is None:
    raise ResourceNotFoundException(f"cant find query engine {query_engine}")

  try:
    # download files to local directory
    storage_client = storage.Client(project=PROJECT_ID)
    doc_filepaths = _download_files_to_local(storage_client, doc_url)

    # ME index name and description
    index_name = query_engine + "-MEindex"
    index_description = \
      "Matching Engine index for LLM Service query engine: " + query_engine

    # bucket for ME index data
    bucket_name = f"{query_engine}-me-data"
    bucket = storage_client.create_bucket(bucket_name)
    bucket_uri = f"gs://{bucket.name}"

    # use langchain text splitter
    text_splitter = CharacterTextSplitter(chunk_size=CHUNK_SIZE,
                                          chunk_overlap=0)

    # counter for unique index ids
    index_base = 0

    # add embeddings for each doc to index data stored in bucket
    for doc in doc_filepaths:
      doc_name, doc_url, doc_filepath = doc
      Logger.info(f"generating index data for {doc_name}")

      # read doc data and split into text chunks
      # skip any file that can't be read or generates an error
      try:
        doc_text_list = _read_doc(doc_name, doc_filepath)
        if doc_text_list is None:
          continue
      except Exception:
        continue

      # split text into chunks
      text_chunks = []
      for text in doc_text_list:
        text_chunks.extend(text_splitter.split_text(text))

      # generate embedding data and store in local dir
      new_index_base, embeddings_dir = \
          _generate_index_data(doc_name, text_chunks, index_base)

      # copy data files up to bucket
      gcs_adapter.upload_folder(bucket_name, embeddings_dir, bucket_uri)
      Logger.info(f"data uploaded for {doc_name}")

      # store QueryDocument and QueryDocumentChunk models
      query_doc = QueryDocument(query_engine_id = q_engine.id,
                                query_engine = q_engine.name,
                                doc_url = doc_url,
                                index_start = index_base,
                                index_end = new_index_base
                                )
      query_doc.save()

      for i in range(index_base, new_index_base):
        query_doc_chunk = QueryDocumentChunk(
                                  query_document_id = query_doc.id,
                                  index = i,
                                  text = text_chunks[i],
                                  )
        query_doc_chunk.save()

      index_base = new_index_base

    # create ME index
    Logger.info(f"creating matching engine index {index_name}")
    tree_ah_index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
        display_name=index_name,
        contents_delta_uri=bucket_uri,
        dimensions=DIMENSIONS,
        approximate_neighbors_count=150,
        distance_measure_type="DOT_PRODUCT_DISTANCE",
        leaf_node_embedding_count=500,
        leaf_nodes_to_search_percent=80,
        description=index_description,
    )
    Logger.info(f"DONE matching engine index {index_name}")
  except Exception as e:
    raise InternalServerError(str(e)) from e

  # create index endpoint

  # store index in query engine model
  q_engine.index_id = tree_ah_index.index_name
  q_engine.update()


def _download_files_to_local(storage_client, doc_url: str) -> \
    List[Tuple[str, str, List[str]]]:
  """ Download files from GCS to a local tmp directory """
  docs = []
  for blob in storage_client.list_blobs(doc_url):
    # skip directories for now
    if blob.name.endswith("/"):
      continue
    # Create a blob object from the filepath
    with tempfile.TemporaryDirectory() as temp_dir:
      file_path = f"{temp_dir}/{blob.name}"
      os.makedirs(os.path.dirname(file_path), exist_ok=True)
      # Download the file to a destination
      blob.download_to_filename(file_path)
      docs.append((blob.name, blob.path, file_path))
  return docs


def _read_doc(doc_name:str, doc_filepath: str) -> List[str]:
  """ Read document and return content as a list of strings """
  doc_extension = doc_name.split(".")[-1]
  doc_extension = doc_extension.lower()
  doc_text_list = None
  loader = None

  if doc_extension == "txt":
    with open(doc_filepath, "r", encoding="utf-8") as f:
      doc_text = f.read()
    doc_text_list = [doc_text]
  elif doc_extension == "csv":
    loader = CSVLoader(file_path=doc_filepath)
  elif doc_extension == "pdf":
    # read PDF into array of pages
    doc_text_list = []
    with open(doc_filepath, "rb") as f:
      reader = PdfReader(f)
      num_pages = len(reader.pages)
      Logger.info("Reading pdf file {doc_name} with {num_pages} pages")
      for page in range(num_pages):
        doc_text_list.append(reader.pages[page].extract_text())
      Logger.info("Finished reading pdf file {doc_name}")
  else:
    # return None if doc type not supported
    pass

  if loader is not None:
    langchain_document = loader.load()
    doc_text_list = [section.content for section in langchain_document]

  return doc_text_list

def _encode_texts_to_embeddings(
    sentence_list: List[str]) -> List[Optional[List[float]]]:
  """ encode text using Vertex AI embedding model """
  model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
  try:
    embeddings = model.get_embeddings(sentence_list)
    return [embedding.values for embedding in embeddings]
  except Exception:
    return [None for _ in range(len(sentence_list))]


# Generator function to yield batches of text_chunks
def _generate_batches(text_chunks: List[str], batch_size: int
    ) -> Generator[List[str], None, None]:
  """ generate batches of text_chunks """
  for i in range(0, len(text_chunks), batch_size):
    yield text_chunks[i : i + batch_size]


def _get_embedding_batched(
    text_chunks: List[str], api_calls_per_second: int = 10, batch_size: int = 5
) -> Tuple[List[bool], np.ndarray]:
  """ get embbedings for a list of text strings """

  embeddings_list: List[List[float]] = []

  # Prepare the batches using a generator
  batches = _generate_batches(text_chunks, batch_size)

  seconds_per_job = 1 / api_calls_per_second

  with ThreadPoolExecutor() as executor:
    futures = []
    for batch in batches:
      futures.append(
          executor.submit(functools.partial(_encode_texts_to_embeddings), batch)
      )
      time.sleep(seconds_per_job)

    for future in futures:
      embeddings_list.extend(future.result())

  is_successful = [
      embedding is not None for sentence, embedding in zip(
        text_chunks, embeddings_list)
  ]
  embeddings_list_successful = np.squeeze(
      np.stack([embedding for embedding in embeddings_list
                if embedding is not None])
  )
  return is_successful, embeddings_list_successful


def _generate_index_data(doc_name: str, text_chunks: List[str],
                         index_base: int) -> Tuple[int, str]:
  """ generate matching engine index data files in a local directory """

  doc_stem = Path(doc_name).stem

  # generate an np array of chunk IDs starting from index base
  ids = np.arange(index_base, index_base + len(text_chunks))

  # Create temporary folder to write embeddings to
  embeddings_dir = Path(tempfile.mkdtemp())

  # Convert chunks to embeddings in batches, to manage API throttling
  is_successful, chunk_embeddings = _get_embedding_batched(
      text_chunks=text_chunks,
      api_calls_per_second=API_CALLS_PER_SECOND,
      batch_size=ITEMS_PER_REQUEST,
  )
  # create JSON
  embeddings_formatted = [
    json.dumps(
      {
        "id": str(idx),
        "embedding": [str(value) for value in embedding],
      }
    )
    + "\n"
    for idx, embedding in zip(ids[is_successful], chunk_embeddings)
  ]

  # Create output file
  chunk_path = embeddings_dir.joinpath(f"{doc_stem}_index.json")

  # write embeddings for chunk to file
  with open(chunk_path, "w", encoding="utf-8") as f:
    f.writelines(embeddings_formatted)

  # clean up any large data structures
  gc.collect()

  index_base = index_base + len(text_chunks)

  return index_base, embeddings_dir
