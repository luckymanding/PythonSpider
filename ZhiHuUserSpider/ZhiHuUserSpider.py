import requests
from lxml import html
import json
from RedisHandler import RedisHandler
from MongoHandler import MongoHandler
import time


# 只抓取了type为people的用户
class ZhiHuUserSpider:

	def __init__(self):
		self.__headers = {
			'accept': 'application / json, text / plain, * / *',
			'Accept - Encoding': 'gzip, deflate, br',
			'Accept - Language': 'zh - CN, zh;q = 0.8',
			'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
			'Host': 'www.zhihu.com',
			'Referer': 'https://www.zhihu.com/',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
						  'Chrome/61.0.3163.100 Safari/537.36 ',
			'X - UDID': 'AFDC3cbZvguPTk1xbYYtpQt214bsP2px88I ='
		}
		self.__session = requests.session()
		self.__redis_handler = RedisHandler()
		self.__mongo_handler = MongoHandler()
		# self.__mysql_handler = MySqlHandler()
		# 字典的update方法进行并集更新
		self.__session.headers.update(self.__headers)
		self.__session.proxies.update({'HTTP': 'HTTP://49.81.254.120:8118'})

	def get_tree(self, url):
		text = self.__session.get(url).text
		# print(html.fromstring(text).__class__)
		return html.fromstring(text)

	# 获取首页上出现的用户的主页地址并存入redis
	def get_url_token_from_index(self):
		tree = self.get_tree('https://www.zhihu.com/explore')
		users_url = tree.xpath('//a[@class="author-link"]/@href')
		# 只抓取个人账户
		# for url_token in [i[8:] for i in users_url if 'people' in i]:
		# 	print(url_token)
		# return [i[8:] for i in users_url if 'people' in i]

		# 将类型为people的url存入redis
		for u in [i[8:] for i in users_url if 'people' in i]:
			print(u)
			self.__redis_handler.save_url_token(u)

	'''
	通过用户的url_token获取该用户关注的人或者关注该用户的人
	根据is_followers的值来确定获取哪一类
	默认获取用户关注的人的url_token并存入redis
	'''
	def get_follow_url_token(self, url_token, is_following=True):
		follow = 'followees' if is_following else 'followers'
		is_end = False
		next_url = 'https://www.zhihu.com/api/v4/members/'+url_token+'/'+follow+'?' \
			  'include=data%5B*%5D.answer_count%2Carticles_count%2Cgender' \
			  '%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F' \
			  '(type%3Dbest_answerer)%5D.topics&offset=0&limit=20'
		while not is_end:
			# dump和dumps是将python对象转换成json格式；load和loads是将json格式转换成python对象
			text = self.__session.get(next_url).text
			res = json.loads(text)
			# 是否获取了所有的用户, 是bool类型
			is_end = res['paging']['is_end']
			# 下一组20个用户的url
			next_url = res['paging']['next']
			# 存入redis
			# print(type(is_end))
			# print(next_url)
			for u in [user['url_token'] for user in res['data'] if user['type'] == 'people']:
				print(u)
				self.__redis_handler.save_url_token(u)

	'''
	传入一个用户的url_token,将该用户的信息存入mysql
	'''
	def save_info_to_mongo(self, url_token):
		url = 'https://www.zhihu.com/api/v4/members/' + url_token + '?include=' \
			  'locations%2Cemployments%2Cgender%2Ceducations%2Cbusiness%2C' \
			  'voteup_count%2Cthanked_Count%2Cfollower_count%2Cfollowing_count%2C' \
		      'cover_url%2Cfollowing_topic_count%2Cfollowing_question_count%2C' \
		      'following_favlists_count%2Cfollowing_columns_count%2Cavatar_hue%2C' \
		      'answer_count%2Carticles_count%2Cpins_count%2Cquestion_count%2C' \
		      'columns_count%2Ccommercial_question_count%2Cfavorite_count%2C' \
		      'favorited_count%2Clogs_count%2Cmarked_answers_count%2C' \
		      'marked_answers_text%2Cmessage_thread_token%2Caccount_status%2C' \
		      'is_active%2Cis_bind_phone%2Cis_force_renamed%2Cis_bind_sina%2C' \
		      'is_privacy_protected%2Csina_weibo_url%2Csina_weibo_name%2C' \
		      'show_sina_weibo%2Cis_blocking%2Cis_blocked%2Cis_following%2C' \
		      'is_followed%2Cis_org_createpin_white_user%2Cmutual_followees_count%2C' \
		      'vote_to_count%2Cvote_from_count%2Cthank_to_count%2Cthank_from_count%2C' \
		      'thanked_count%2Cdescription%2Chosted_live_count%2Cparticipated_live_count%2C' \
		      'allow_message%2Cindustry_category%2Corg_name%2Corg_homepage%2C' \
		      'badge%5B%3F(type%3Dbest_answerer)%5D.topics'
		text = self.__session.get(url).text
		res = json.loads(text)
		print(text)
		# self.__mongo_handler.save_info(**res)


if __name__ == '__main__':
	spider = ZhiHuUserSpider()
	spider.save_info_to_mongo('WanPlusSW')
