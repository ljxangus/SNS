#-*- coding:utf-8 -*-

import jieba
import jieba.analyse

def extractKeywords(status):

	content = status
	tags = jieba.analyse.extract_tags(content, topK=2)

	print 'The tags are'
	print ",".join(tags)
	return tags