from bs4 import BeautifulSoup
import re  
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
import jieba

def remove_punc(line):
  rule = re.compile(r'[^a-zA-Z0-9\u4e00-\u9fa5]')
  line = rule.sub('',line)
  return line

# 去停用词 
stopwords=[]   # 加载中文停用词

with open('./哈工大停用词表.txt', 'r', encoding='UTF-8') as f:
  temp = f.read()
  for word in temp:
    # 去除换行符
    stopwords.append(word.strip())



def cut_sent(para):
  sents = re.split('(。|！|\!|\.|？|\?)', para)   #有分隔符
  new_sent = []
  for i in range(int(len(sents)/2)):
    sent = sents[2*i] + sents[2*i+1]    #形成带标点符号的完整句子
    new_sent.append(sent)

  return new_sent   
  


def Get_key_sents(paragraph):

  sent2words_with_punc = []
  sent2words = []
  for i in cut_sent(paragraph):
    a = remove_punc(i)
    txt1 = jieba.cut(a,cut_all=False)
    txt1 = [word for word in txt1 if word not in stopwords]
    sent2words.append(txt1)
    sent2words_with_punc.append(i)

  vectoerizer = CountVectorizer(token_pattern='\\b\\w+\\b')

  corpus1 = []
  for i in sent2words:
    str_sent = ' '.join(i)
    corpus1.append(str_sent)

  vectoerizer.fit(corpus1)
  bag_of_words = vectoerizer.get_feature_names()

  def compute_sent_score(sent):
    score=[]
    for word in sent:
      idx = bag_of_words.index(word)
      tfidf_score = tfidf_transformer.idf_[idx]
      score.append(tfidf_score)
      sent_score = sum(score)/len(score)
    return sent_score

  X = vectoerizer.transform(corpus1)

  # transform tfidf
  tfidf_transformer = TfidfTransformer()
  tfidf_transformer.fit(X.toarray())

  score_list = []
  for sent in sent2words:
    score_list.append(compute_sent_score(sent))


  f = max(score_list)   # 取出所有最高分数的句子
  idx = [i for i, j in enumerate(score_list) if j == f]
  score_list.remove(f)

  key_sents = []
  for i in idx:
    key_sents.append(sent2words_with_punc[i])

  s = max(score_list)
  idx = [i for i, j in enumerate(score_list) if j == s]
  for i in idx:
    key_sents.append(sent2words_with_punc[i])
  
  return key_sents
    

def main(pa):
  res = Get_key_sents(pa)
  return res

if __name__ == '__main__':
  print('please input text: ')
  pa = input()
  ret = main(pa)
  print(ret)
  print('success')