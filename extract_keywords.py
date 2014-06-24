import jieba
import jieba.analyse

def extractKeywords(status):

	content = status
	tags = jieba.analyse.extract_tags(content, topK=3)

	print ",".join(tags)
	return tags