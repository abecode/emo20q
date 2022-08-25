#!/usr/bin/env python3


""" 
this is the basic question answering functionality

answer a question about an emotion
"""

import os

# for tensorflow/bert
import numpy as np
import tensorflow as tf
# !pip install -q tf-models-official==2.4.0
from official.nlp import bert
import official.nlp.bert.tokenization


# Set up tokenizer to generate Tensorflow dataset

# # for desktop:
# os.environ['NO_GCE_CHECK'] = 'true'
# # note: this is from the training pipeline
# # it only uses the tokenizer and vocab
# gs_folder_bert = "gs://cloud-tpu-checkpoints/bert/v3/uncased_L-12_H-768_A-12"
# tokenizer = bert.tokenization.FullTokenizer(
#    vocab_file=os.path.join(gs_folder_bert, "vocab.txt"),
#     do_lower_case=True)
# export_dir = "/Users/kaze7539/Downloads/saved_model_bert_emo20qa"
# model  = tf.saved_model.load(export_dir)

# for aws
tokenizer = bert.tokenization.FullTokenizer(
   vocab_file="vocab.txt",
     do_lower_case=True)
export_dir = "/home/ec2-user/saved_model_bert_emo20qa"
model  = tf.saved_model.load(export_dir)

lab2id = {"no":0, "maybe":1, "yes":2}
id2lab = {v:k for k,v in lab2id.items()}

def encode_sentence2(s):
   tokens = list(tokenizer.tokenize(s))
   tokens.append('[SEP]')
   return tokenizer.convert_tokens_to_ids(tokens)

def bert_encode2(data_dict):
  num_examples = len(data_dict["emotion"])
  
  sentence1 = tf.ragged.constant([
      encode_sentence2(s)
      for s in np.array(data_dict["emotion"])])
  sentence2 = tf.ragged.constant([
      encode_sentence2(s)
       for s in np.array(data_dict["question"])])

  cls = [tokenizer.convert_tokens_to_ids(['[CLS]'])]*sentence1.shape[0]
  input_word_ids = tf.concat([cls, sentence1, sentence2], axis=-1)

  input_mask = tf.ones_like(input_word_ids).to_tensor()

  type_cls = tf.zeros_like(cls)
  type_s1 = tf.zeros_like(sentence1)
  type_s2 = tf.ones_like(sentence2)
  input_type_ids = tf.concat(
      [type_cls, type_s1, type_s2], axis=-1).to_tensor()

  inputs = {
      'input_word_ids': input_word_ids.to_tensor(),
      'input_mask': input_mask,
      'input_type_ids': input_type_ids}

  return inputs

def answer_emotion_question(emotion, question):
    encoded = bert_encode2({"emotion": [emotion], "question": [question]})
    res = model([encoded['input_word_ids'],
                 encoded['input_mask'],
                 encoded['input_type_ids']], training=False)
    answer = id2lab[int(tf.argmax(res, axis=1)[0])]
    return answer

if __name__ == "__main__":
    import argparse
    argParser = argparse.ArgumentParser(description="""A generalized pushdown automaton implementation of an EMO20Q questioner agent.  """)
    argParser.add_argument('-t', '--test',
                           action='store_true',
                           help='test using doctest')
    argParser.add_argument('--run',
                           action='store_true',
                           help='run the agent interactively on the commandline')
    args = argParser.parse_args()
    if args.test:
        import doctest
        doctest.testmod()
    #elif args.run:
    else:
        emotion_prompt = "enter an emotion: "
        question_prompt = "enter a question: "
        prev_emotion = ""
        prev_question = ""
        while True:
            emotion = input(emotion_prompt)
            question = input(question_prompt)
            emotion = emotion if emotion else prev_emotion
            question = question if question  else prev_question
            print(answer_emotion_question(emotion, question))
            emotion_prompt = "enter an emotion or hit return to use the previous: "
            question_prompt = "enter a question or hit return to use the previous: "
            prev_emotion = emotion
            prev_question = question
