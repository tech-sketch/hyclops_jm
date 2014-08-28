#!/usr/bin/env python
#-*- coding: utf-8 -*

"""
ZabbixとJobSchedulerの連携プログラム
  １．$Z4J_HOME/live配下にJobSchedulerに登録したJob情報を置くと
　　１）JobSchedulerにJobを登録する。
    ２）ZabbixにJobとJob Chainの実行時間を監視するアイテムと実行結果を
        監視するアイテムとその実行結果からアラートを上げるトリガを登録
        する。
  ２．外部スクリプトを実行したときに、上記のアイテムにzabbix_senderで
      登録する。
  ３．ジョブが実行したときにトリガの設定を一時的に変更する。
         （注意）テンプレートを使用して明示的に実行する必要があります。

"""

__author__  = "Mitsuyuki Kato, OSSLab inc."
__version__ = "1.00"
__date__    = "2014/06/30"


#############################################################
# インポートモジュール
#############################################################

#============================================================
# For Base
from fabric.api import lcd, cd, local, env, hide
import sys, os, os.path, time, fnmatch
from datetime import datetime as dt
from datetime import datetime

#============================================================
# For soap
import httplib

#============================================================
# For socket
import socket
from contextlib import closing

#============================================================
# For xml
from xml.dom import minidom
from StringIO import StringIO
import xml.etree.ElementTree as ET
from xml.etree import ElementTree

#============================================================
# For json
import json

#============================================================
# For PostgreSQL
import psycopg2


#############################################################
# システム情報
#############################################################
# 値はデフォルト値　実際に使うのはDB情報
env.jos_server="localhost"
env.jos_port=4444
env.zbx_server="localhost"
env.zbx_login="Admin"
env.zbx_pass="zabbix"

#============================================================
# DBへの接続情報
env.psqldatabase='zbx4jos'
env.psqluser='OSSLUSER'
env.psqlpassword='OSSLUSER'
env.psqlhost='127.0.0.1'
env.psqlport=5432

env.jos_timeout=5
env.dbg=1

#############################################################
# グローバルバッファ
#############################################################

env.job_list={}
env.job_dirs={}
env.jos_server_list={}
env.jos_job=[]
env.jos_job_chain=[]
env.jos_order={}
env.process_class={}
env.zbx_server_list={}
env.zbx_id=100
env.inited=0
env.jos_last_id={}


#############################################################
# ライブラリ モジュール
#############################################################

#============================================================
def help():
	print "zbx4jos <コマンド>[:パラメータ[,パラメータ].....]"
	print ""
	print "[コマンド]"
	print "	show_info	： JobSchedulerからジョブ情報を取得してzabbix_senderで"
	print "				Zabbixにジョブの処理時間を送信する"
	print "	set_job_items	： Zabbixにジョブのitemを設定する"
	print "	get_jobs    	： Level Discavery用にジョブ情報をJSONで表示する"
	print "	trigger_switch	： 現状のTriggerを無効にして代わりを設定する"
	print "		[パラメータ]	： hostid	： 無効にするホストID"
	print "				　 msg		： 無効にするトリガ名"
	print "				　 rule		： 無効後に登録するトリガ条件"
	print "	trigger_ret	： trigger_switchで設定した内容を元に戻す"
	print "		[パラメータ]	： hostid	： 有効にするホストID"
	print "				　 msg		： 元に戻すトリガ名"


#############################################################
# ライブラリ モジュール
#############################################################

#============================================================
def getdbinfo(dbg=0):
	"""
	getdbinfo
	PostgreSQLからシステム情報を取得
	@param		： None

	@reruen		： None
	"""

	if env.inited == 1:				# 複数回呼ばれても１回しか実行しない
		return

	connection = psycopg2.connect(
	 database = env.psqldatabase,
	 user = env.psqluser,
	 password = env.psqlpassword,
	 host = env.psqlhost,
	 port = env.psqlport)

	cur = connection.cursor()			# DBへの接続

	cur.execute("SELECT * FROM sysinfo")		# システム情報の取得

	for row in cur:
		if dbg == "1":
			print("%s : %s" % (row[0], row[1]))

		if row[0] == 'jos_server':
			env.jos_server=row[1]
		elif row[0] == 'jos_port':
			env.jos_port=int(row[1],10)
		elif row[0] == 'zbx_server':
			env.zbx_server=row[1]
		elif row[0] == 'zbx_login':
			env.zbx_login=row[1]
		elif row[0] == 'zbx_pass':
			env.zbx_pass=row[1]
		elif row[0] == 'jos_timeout':
			env.zbx_timeout=int(row[1],10)

	cur.execute("SELECT * FROM jobid_tbl")		# 前回実行時のTask IDの取得

	for row in cur:
		if dbg == "1":
			print("%s : %s" % (row[0], row[1]))

		env.jos_last_id[row[0]] = row[1]


	cur.close()					# DBへの切断
	connection.close()

	env.inited = 1					# 複数回呼び出しの対応

#============================================================
def getzbx(SoapMessage,dbg=0):
	"""
	getzbx
	Zabbix APIにJSON-RPCでアクセスする
	@param	SoapMessage	： Zabbixへ送信するJSON-RPCコマンド

	@reruen	res		： Zabbixからの返信
	"""

	getdbinfo(dbg)

	#construct and send the header

	webservice = httplib.HTTP("%s" % (env.zbx_server) )
	webservice.putrequest("POST", "/zabbix/api_jsonrpc.php")
	webservice.putheader("Host", "172.0.0.1")
	webservice.putheader("User-Agent", "Python post")
	webservice.putheader("Content-type", "application/json-rpc")
	webservice.putheader("Content-length", "%d" % len(SoapMessage))
	webservice.endheaders()
	webservice.send(SoapMessage)

	# get the response

	statuscode, statusmessage, header = webservice.getreply()
	res = webservice.getfile().read()

	return res

#============================================================
def getzbx_login(id,dbg=0):
	"""
	getzbx_login
	Zabbixから認証情報を取得する
	@param	id		： id情報

	@reruen	auth_data	： Zabbixから取得した認証情報
	"""

	getdbinfo(dbg)

	# a "as lighter as possible" soap message:

	SM_TEMPLATE_AUTH = """{"auth":null,"method":"user.login","id":%s,"params":
	{"user":"%s","password":"%s"},"jsonrpc":"2.0"}"""

	SoapMessage = SM_TEMPLATE_AUTH % (id,env.zbx_login,env.zbx_pass)
	if dbg == "1":
		print SoapMessage
	res = getzbx( SoapMessage,dbg )

	if dbg == "1":
		print res

	recvbuf = json.loads(res)
	auth_data = recvbuf['result']

	return auth_data

#============================================================
def jos_soap(SoapMessage,dbg=0):
	"""
	jos_soap
	JobSchedulerにsoapでアクセスする
	@param	SoapMessage	： JobSchedulerへsoapで送信する

	@reruen	auth_data	： JobSchedulerから取得した情報
	"""

	getdbinfo(dbg)

	#construct and send the header

	webservice = httplib.HTTP("%s:%s" % (env.jos_server,env.jos_port) )
	webservice.putrequest("POST", "/scheduler")
	webservice.putheader("Host", "%s") % env.jos_server
	webservice.putheader("User-Agent", "Python post")
	webservice.putheader("Content-type", "application/soap+xml;charset=UTF-8")
	webservice.putheader("Content-length", "%d" % len(SoapMessage))
	webservice.putheader("SOAPAction", "\"\"")
	webservice.endheaders()
	webservice.send(SoapMessage)

	# get the response

	statuscode, statusmessage, header = webservice.getreply()
	print "Response: ", statuscode, statusmessage
	print "headers: ", header
	res = webservice.getfile().read()

	if dbg == '1':
		print res

	return res

#============================================================
def jos_xml(XmlMessage,dbg=0):
	"""
	jos_xml
	JobSchedulerにXMLコマンドを送信する
	@param	SoapMessage	： JobSchedulerへ送信するXMLコマンド

	@reruen	auth_data	： JobSchedulerから取得した情報
	"""

	dbg = env.dbg
	getdbinfo(dbg)

	bufsize = 524288

	if dbg == "1":
		print 'jos_xml Command : ',XmlMessage

	recvbuf = ''
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(env.jos_timeout)
	with closing(sock):
		sock.connect((env.jos_server, env.jos_port))
		sock.send(b'%s' % XmlMessage)
		while 1:
			try:
				tmp = sock.recv(bufsize)
			except socket.timeout:
				if dbg == "1":
					print 'End Timeout'
				break

			if not tmp:
				if dbg == "1":
					print 'End'
				break

			recvbuf = recvbuf + tmp

	if dbg == "1":
		print "===< jos_xml >==="
		print recvbuf
		print "===< jos_xml >==="

	while recvbuf[-1:] <> '>':				# 最後の文字が">"になるまで削除
		tmpbuf = recvbuf[:-1]
		recvbuf = tmpbuf

	tmpbuf = recvbuf.replace('&', '#amp')			# ＆がエラーとなるための回避
	recvbuf = tmpbuf

	return recvbuf

#============================================================
# XMLフォーマットの情報をすべて表示する

def printAllElement(node, hierarchy=1):
	"""
	printAllElement
	XMLフォーマットの情報をすべて表示する
	@param	node	： ID情報
	@param	hierarcy： 表示するときのTABの数

	@reruen		： None
	"""

	# スペース調整
	space = ''
	for i in range(hierarchy*4):
		space += ' '

	# エレメントノードの場合はタグ名を表示する
	if node.nodeType == node.ELEMENT_NODE:
		print("{0}{1}".format(space, node.tagName))
		if node.attributes.keys():
			for attr in node.attributes.keys():
				print("ATTR{0}  --{1} : {2}".\
					format(space,node.attributes[attr].name,\
					node.attributes[attr].value))
		# 再帰呼び出し
		for child in node.childNodes:
			printAllElement(child, hierarchy+1)

	# テキストもしくはコメントだった場合dataを表示する
	elif node.nodeType in [node.TEXT_NODE, node.COMMENT_NODE]:
	# スペースを取り除く
		data = node.data.replace(' ', '')

		# 改行のみではなかった時のみ表示する
		if data!='\n':
			print("PARA{0}<{1}>".format(space, node.data))



#############################################################
# サブルーティン関数
#############################################################

#============================================================

def zbx_getitems(hostid="10084",dbg=0):
	"""
	zbx_getitems
	Zabbixから指定したホストのitem情報を得る
	@param	hostid		： 取得するアイテムのhostid

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	id = env.zbx_id

	# a "as lighter as possible" soap message:

	SM_TEMPLATE_ITEM_GET = """{ "jsonrpc": "2.0", "method": "item.get", "params": {
        "output": "extend", "hostids": "%s",
        "sortfield": "name" }, "auth":"%s", "id": %s } """

	auth_data = getzbx_login(id)

	SoapMessage = SM_TEMPLATE_ITEM_GET % (hostid, auth_data, id)
	res = getzbx( SoapMessage )
	recvbuf = json.loads(res)

	if dbg == '1':
		print json.dumps(recvbuf, indent=4)			# print All elements of JSON

	return recvbuf


#============================================================

def zbx_item_exist(keys,hostid,dbg=0):
	"""
	zbx_item_exist
	Zabbixに指定したホストに指定したitemが有るかを確認する
	@param	keys		： 確認するアイテムのKay
	@param	hostid		： 確認するアイテムのhostid

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	id = env.zbx_id

	# a "as lighter as possible" soap message:

	SM_TEMPLATE_ITEM_EXIST = """ { "jsonrpc": "2.0", "method": "item.exists", "params": {
	"hostid": "%s", "key_": "%s"
	}, "auth": "%s", "id": %s } """

	auth_data = getzbx_login(id)

	SoapMessage = SM_TEMPLATE_ITEM_EXIST % (keys,hostid, auth_data, id)
	res = getzbx( SoapMessage )
	recvbuf = json.loads(res)

	if dbg == '1':
		print json.dumps(recvbuf, indent=4)			# print All elements of JSON

	return recvbuf


#============================================================

def zbx_setitems(name,hostid="10084",dbg=0):
	"""
	zbx_setitems
	Zabbixに指定したホストにitemを設定する
	@param	name		： 確認するアイテムのKay（アイテム名）
	@param	hostid		： 確認するアイテムのhostid

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	id = env.zbx_id

	# a "as lighter as possible" soap message:

	SM_TEMPLATE_ITEM_SET = """ { "jsonrpc": "2.0", "method": "item.create", "params": {
        "name": "Jobscheduler's Job (%s)", "key_": "%s", "hostid": "%s", "type": 2,
        "value_type": 3, "interfaceid": "0", "delay": 30
	}, "auth": "%s", "id": %s } """

	auth_data = getzbx_login(id)

	SoapMessage = SM_TEMPLATE_ITEM_SET % (name,name,hostid, auth_data, id)
	res = getzbx( SoapMessage )
	recvbuf = json.loads(res)

	if dbg == '1':
		print json.dumps(recvbuf, indent=4)			# print All elements of JSON

	return recvbuf


#============================================================

def zbx_delitems(itemid,dbg=0):
	"""
	zbx_delitems
	Zabbixから指定したitemを削除する
	@param	hostid		： 削除するアイテムのhostid

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	id = env.zbx_id

	# a "as lighter as possible" soap message:

	SM_TEMPLATE_ITEM_SET = """ { "jsonrpc": "2.0", "method": "item.delete", "params": [
	"%s" ], "auth": "%s", "id": %s } """

	auth_data = getzbx_login(id)

	SoapMessage = SM_TEMPLATE_ITEM_SET % (itemid, auth_data, id)
	res = getzbx( SoapMessage )
	recvbuf = json.loads(res)

	if dbg == '1':
		print json.dumps(recvbuf, indent=4)			# print All elements of JSON

	return recvbuf


#============================================================

def zbx_gettrigger(hostid="10084",dbg=0):
	"""
	zbx_gettrigger
	Zabbixから指定したホストのtrigger情報を取得する
	@param	hostid		： 取得するするトリガのhostid

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	id = env.zbx_id

	# a "as lighter as possible" soap message:

	SM_TEMPLATE_ITEM_GET2 = """{ "jsonrpc": "2.0", "method": "trigger.get", "params": {
	"output": "extend", "hostids": "%s", "selectFunctions": "extend"
	}, "auth": "%s", "id": %s } """

	SM_TEMPLATE_ITEM_GET = """{ "jsonrpc": "2.0", "method": "trigger.get", "params": {
	"output": "extend",
	"expandExpression": "True",
	"hostids": "%s"
	}, "auth": "%s", "id": %s } """

	auth_data = getzbx_login(id)

	SoapMessage = SM_TEMPLATE_ITEM_GET % (hostid, auth_data, id)
	if dbg in ["1","2"]:
		print SoapMessage
	res = getzbx( SoapMessage )
	recvbuf = json.loads(res)

	if dbg == '1':
		print json.dumps(recvbuf, indent=4)			# print All elements of JSON

	return recvbuf


#============================================================

def zbx_settrigger(hostid,exp,desp,pri=3,dbg=0):
	"""
	zbx_settrigger
	Zabbixに指定したホストに指定したtriggerを設定する
	@param	hostid		： 設定するするトリガのhostid
	@param	exp		： 設定するするトリガ名
	@param	desp		： 設定するするトリガの条件情報
	@param	pri		： 設定するするトリガのプラオリティ（デフォルト3）

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	id = env.zbx_id

	# a "as lighter as possible" soap message:

	SM_TEMPLATE_ITEM_SET = """ { "jsonrpc": "2.0", "method": "trigger.create", "params": {
        "priority": "%s", 
	"description": "%s", 
	"hosts": [ { "hostid": "%s" } ], 
	"expression": "%s"
	}, "auth": "%s", "id": %s } """

	auth_data = getzbx_login(id)

	SoapMessage = SM_TEMPLATE_ITEM_SET % (pri,desp,hostid,exp,auth_data,id)
	if dbg in ["1","2"]:
		print SoapMessage

	res = getzbx( SoapMessage )
	recvbuf = json.loads(res)

	if dbg == '1':
		print json.dumps(recvbuf, indent=4)			# print All elements of JSON

	return recvbuf


#============================================================

def zbx_deltrigger(tid,dbg=0):
	"""
	zbx_deltrigger
	Zabbixに指定したホストに指定したtriggerを削除する
	@param	tid		： 削除するするトリガID

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	id = env.zbx_id

	# a "as lighter as possible" soap message:

	SM_TEMPLATE_ITEM_SET = """ { "jsonrpc": "2.0", "method": "trigger.delete", "params": [
	"%s"
	], "auth": "%s", "id": %s } """

	auth_data = getzbx_login(id)

	SoapMessage = SM_TEMPLATE_ITEM_SET % (tid,auth_data,id)
	if dbg in ["1","2"]:
		print SoapMessage

	res = getzbx( SoapMessage )
	recvbuf = json.loads(res)

	if dbg == '1':
		print json.dumps(recvbuf, indent=4)			# print All elements of JSON

	return recvbuf


#============================================================

def zbx_gethosts(dbg=0):
	"""
	zbx_gethosts
	Zabbixから設定されているホスト情報を取得する
	@param	None		： 

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	id = env.zbx_id

	# a "as lighter as possible" soap message:

	SM_TEMPLATE_HOST_GET = """{ "jsonrpc": "2.0", "method": "host.get", "params": { "output": "extend"
	}, "auth": "%s", "id": %s }"""


	auth_data = getzbx_login(id)

	SoapMessage = SM_TEMPLATE_HOST_GET % (auth_data, id)
	res = getzbx( SoapMessage )
	recvbuf = json.loads(res)

	if dbg == '1':
		print json.dumps(recvbuf, indent=4)			# print All elements of JSON

	return recvbuf

#============================================================

def zbx_gethost(hostname,dbg=0):
	"""
	zbx_gethost
	Zabbixに指定したホストがあるかを確認する
	@param	hostname	： 確認するhost名

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	id = env.zbx_id

	# a "as lighter as possible" soap message:

	SM_TEMPLATE_HOST_GET = """{ "jsonrpc": "2.0", "method": "host.get", "params": { "output": "extend",
	"filter": { "host": "%s" }
	}, "auth": "%s", "id": %s }"""

	auth_data = getzbx_login(id)

	SoapMessage = SM_TEMPLATE_HOST_GET % (hostname, auth_data, id)
	res = getzbx( SoapMessage )
	recvbuf = json.loads(res)

	if dbg == '1':
		print json.dumps(recvbuf, indent=4)			# print All elements of JSON

	return recvbuf

#============================================================

def gettriggerid(hostid,msg,dbg=0):
	"""
	gettriggerid
	Trigger一覧を取得する
	@param	hostid		： 確認するhost名
	@param	msg		： 確認するトリガ情報

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	recvbuf = zbx_gettrigger(hostid,1)
	recvkeys = recvbuf.keys()

	if dbg == '1':
		print " Search msg : ",msg

	ret = ''

	for k in recvkeys:
		if k == 'result':
			i = 0
			maxpoint = recvbuf[k]
			max = len(maxpoint)
			while i < max:
				results = recvbuf[k][i]
				reskeys = results.keys()
				if dbg == '1':
					print "  description : ",results['description']
				if msg in results['description']:
					ret = results['triggerid']
					if dbg == '1':
						print "     Matched"

				i = i + 1

	if dbg == '1':
		print ret

	return ret

#============================================================

def gettrigger_enable(tid,dbg=0):
	"""
	gettrigger_enable
	Triggerを有効にする
	@param	tid		： 有効にするトリガID

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	id = env.zbx_id

	# a "as lighter as possible" soap message:

	SM_TEMPLATE_ITEM_GET = """ { "jsonrpc": "2.0", "method": "trigger.update", "params": {
	"triggerid": "%s",
	"status": 0
	}, "auth": "%s", "id": %s } """

	auth_data = getzbx_login(id)

	SoapMessage = SM_TEMPLATE_ITEM_GET % (tid, auth_data, id)
	res = getzbx( SoapMessage )
	recvbuf = json.loads(res)

	if dbg == '1':
		print json.dumps(recvbuf, indent=4)			# print All elements of JSON

	return recvbuf


#============================================================

def gettrigger_disable(tid,dbg=0):
	"""
	gettrigger_enable
	Triggerを無効にする
	@param	tid		： 無効にするトリガID

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	id = env.zbx_id

	# a "as lighter as possible" soap message:

	SM_TEMPLATE_ITEM_GET = """ { "jsonrpc": "2.0", "method": "trigger.update", "params": {
	"triggerid": "%s",
	"status": 1
	}, "auth": "%s", "id": %s } """

	auth_data = getzbx_login(id)

	SoapMessage = SM_TEMPLATE_ITEM_GET % (tid, auth_data, id)
	res = getzbx( SoapMessage )
	recvbuf = json.loads(res)

	if dbg == '1':
		print json.dumps(recvbuf, indent=4)			# print All elements of JSON

	return recvbuf


#============================================================

def jos_runjob(jobname,dbg=0):
	"""
	jos_runjob
	JobSchedulerにJob実行のxmlコマンドを送信する
	@param	jobname		： 実行するジョブ名

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	# a "as lighter as possible" soap message:

	SM_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
	<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
	<soapenv:Body>
	<startJob xmlns="http://www.sos-berlin.com/scheduler">
	<job>%s</job>
	<at>now</at>
	</startJob>
	</soapenv:Body>
	</soapenv:Envelope>
	"""

	SoapMessage = SM_TEMPLATE % (jobname)

	res = jos_soap(SoapMessage)

	print res

#============================================================

def jos_show_history(jobname,tid,dbg=0):
	"""
	jos_show_history
	JobSchedulerから指定したJobの履歴を取得する
	@param	jobname		： 取得する履歴のするジョブ名
	@param	tid		： 取得する履歴のジョブに対するタスクID

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	recvbuf = jos_xml(('<show_history job="%s" id="%d" next="100" />' % (jobname,tid)))
	root = ET.fromstring(recvbuf)

	if dbg == '1':
		xmldoc = minidom.parseString(recvbuf)
		printAllElement(xmldoc.documentElement)

	return root

#============================================================

def jos_show_state(dbg=0):
	"""
	jos_show_state
	JobSchedulerからステータス情報を取得する
	@param	None		： 

	@reruen	recvbuf		： Zabbixから取得した情報
	"""

	getdbinfo(dbg)

	recvbuf = jos_xml('<show_state />')
	if dbg == '1':
		print "===< jos_show_state >==="
		print recvbuf
		print "===< jos_show_state >==="
	root = ET.fromstring(recvbuf)

	if dbg == '1':
		xmldoc = minidom.parseString(recvbuf)
		printAllElement(xmldoc.documentElement)

	return root


#============================================================

def jos_set_server(dbg=0):
	"""
	jos_set_server
	JobSchedulerに使用されてるprocess_classの情報を取得する
	@param	None		： 

	@reruen	None		： （env.jos_server_listに情報を設定する）
	"""

	getdbinfo(dbg)

	check_jobfile()

	path = "%s/%s" % (os.getenv("Z4J_HOME"), "live")
	if dbg in ["1","2"]:
		print "PATH = ",path

	for job in env.job_list:
		file = "%s/%s" % (path, job)
		if '.process_class.xml' in file:		# process_classファイルだけ処理をする。
			if dbg in ["1","2"]:
				print file

			xdoc = minidom.parse(file)

			elem = xdoc.getElementsByTagName('process_class')
			for s in elem :
				if s.hasAttribute("remote_scheduler"):
					proc_serv = os.path.basename(job).replace('.process_class.xml','')
					env.jos_server_list[proc_serv] = s.attributes['remote_scheduler'].value

	if dbg in ["1","2"]:
		print json.dumps(env.jos_server_list,indent=4)



#============================================================

def set_job_info(dbg=0):
	"""
	jos_set_server
	JobSchedulerに登録するJob情報を解析してZabbixに登録するitem情報を取得する
	@param	None		： 

	@reruen	None		： （env.process_classに情報を設定する）
	"""

	getdbinfo(dbg)

	path = "%s/%s" % (os.getenv("Z4J_HOME"), "live")
	if dbg in ["1","2"]:
		print "PATH = ",path

	for job in env.job_list:
		if '.job.xml' in job:				# JOBファイルだけ処理をする。
			if env.job_list[job] != "DEL":
				file = "%s%s" % (path, job)
				job = job.replace('.job.xml','')
				env.jos_job.append(job)

				xdoc = minidom.parse(file)

				elem = xdoc.getElementsByTagName('job')
				for s in elem :
					env.jos_order[job] = 'no'
					if s.hasAttribute("order"):
						env.jos_order[job] = s.attributes['order'].value

					env.process_class[job] = env.jos_server
					if s.hasAttribute("process_class"):
						env.process_class[job] = env.jos_server_list[s.attributes['process_class'].value]
						tmp = env.process_class[job].split(':')
						env.process_class[job] = tmp[0]

	if dbg in ["1","2"]:
		for job in env.jos_job:
			print job
			print '   process_class = %s' % env.process_class[job]
			print '   order = %s' % env.jos_order[job]

#============================================================

def set_job_chain_info(dbg=0):
	"""
	set_job_chain_info
	JobSchedulerに登録するJob Chain情報を解析してZabbixに登録するitem情報を取得する
	@param	None		： 

	@reruen	None		： （env.process_classに情報を設定する）
	"""

	getdbinfo(dbg)


	path = "%s/%s" % (os.getenv("Z4J_HOME"), "live")
	if dbg in ["1","2"]:
		print "PATH = ",path

	for job in env.job_list:
		if '.job_chain.xml' in job:				# JOBファイルだけ処理をする。
			if env.job_list[job] != "DEL":
				file = "%s%s" % (path, job)
				job = job.replace('.job_chain.xml','')
				env.jos_job_chain.append(job)

				xdoc = minidom.parse(file)

				elem = xdoc.getElementsByTagName('job_chain')
				for s in elem :
					env.process_class[job] = env.jos_server
					if s.hasAttribute("process_class"):
						env.process_class[job] = env.jos_server_list[s.attributes['process_class'].value]
						tmp = env.process_class[job].split(':')
						env.process_class[job] = tmp[0]

	if dbg in ["1","2"]:
		for job in env.jos_job_chain:
			print job
			print '   process_class = %s' % env.process_class[job]

#============================================================

def check_jobfile(dbg=0):
	"""
	check_jobfile
	登録するジョブ情報と現状のジョブ情報を比較してジョブの登録、修正、削除を解析する
	@param	None		： （$Z4J_HOME/live、$SCHEDULER_DATA/config/live配下のファイル）

	@reruen	None		： （env.job_listに情報を設定する）
	"""

	regist_size={}
	regist_time={}
	live_size={}
	live_time={}

	regist_dirs={}
	live_dirs={}

	getdbinfo(dbg)

	path = "%s/%s" % (os.getenv("Z4J_HOME"), "live")	# 登録情報のディレクトリを取得
	if dbg in ["1","2"]:
		print "PATH = ",path

	for root, dirs, files in os.walk(path):			# 登録するファイルの情報取得
	    for file in files:
		if fnmatch.fnmatch(file, '*.xml'):
			file = os.path.join(root, file)
			n = file.replace(path,'')
		##	n = n.replace('/','.')
			regist_size[n] = os.stat(file).st_size
			regist_time[n] = os.stat(file).st_mtime

	path = "%s/%s" % (os.getenv("SCHEDULER_DATA"), "config/live")	# 現状ディレクトリを取得
	if dbg in ["1","2"]:
		print "PATH = ",path

	for root, dirs, files in os.walk(path):			# 現状ファイルの情報取得
	    for dirs in files:
		if fnmatch.fnmatch(file, '*.xml'):
			file = os.path.join(root, dirs)
			n = file.replace(path,'')
		##	n = n.replace('/','.')
			live_size[n] = os.stat(file).st_size
			live_time[n] = os.stat(file).st_mtime

	for rf in regist_size:					# ファイル情報を比較
		mode = "NONE"
		if live_size.has_key(rf):			# サイズ、日付が違う場合は修正
			if live_size[rf] != regist_size[rf]:
				mode = "MOD"
			elif live_time[rf] != regist_time[rf]:
				mode = "MOD"
		else:						# 現状に無い場合は追加
			mode = "ADD"

		env.job_list[rf] = mode

		if dbg in ["2"]:
			print mode," : ",rf
			print "  REG   size=",regist_size[rf]," : time=",time.ctime(regist_time[rf])
			if mode != "ADD":
				print "  LIV   size=",live_size[rf]," : time=",time.ctime(live_time[rf])

	for rf in live_size:					# 登録ディレクトリにだけある場合は削除
		if regist_size.has_key(rf) == 0:
			env.job_list[rf] = "DEL"
			if dbg in ["2"]:
				print "DEL : ",rf
				print "  LIV   size=",live_size[rf]," : time=",time.ctime(live_time[rf])

	if dbg in ["1","2"]:
		print json.dumps(env.job_list,indent=4)


	path = "%s/%s" % (os.getenv("Z4J_HOME"), "live")	# 登録情報のディレクトリを取得
	if dbg in ["1","2"]:
		print "PATH = ",path

	for root, dirs, files in os.walk(path):			# 登録するディレクトリの情報取得
	    n = root.replace(path,'')
	    regist_dirs[n] = n

	path = "%s/%s" % (os.getenv("SCHEDULER_DATA"), "config/live")	# 現状ディレクトリを取得
	if dbg in ["1","2"]:
		print "PATH = ",path

	for root, dirs, files in os.walk(path):			# 現状ディレクトリの情報取得
	    n = root.replace(path,'')
	    live_dirs[n] = n

	for rd in regist_dirs:					# ファイル情報を比較
		mode = "ADD"
		for ld in live_dirs:
			if rd == ld:
				mode = "NONE"

		if mode == "ADD":
			env.job_dirs[rd] = mode

			if dbg in ["1","2"]:
				print "DIR = ",rd," mode = ",mode

	for ld in live_dirs:					# ファイル情報を比較
		mode = "DEL"
		for rd in regist_dirs:
			if rd == ld:
				mode = "NONE"

		if mode == "DEL":
			env.job_dirs[ld] = mode
			if dbg in ["1","2"]:
				print "DIR = ",ld," mode = ",mode

	if dbg in ["1","2"]:
		print json.dumps(env.job_dirs,indent=4)

#============================================================

def set_copy_jobs(dbg=0):
	"""
	set_copy_jobs
	JobSchedulerへの登録情報ファイルと現状ファイルを合わせる
	@param	None		： （$Z4J_HOME/live、$SCHEDULER_DATA/config/live配下のファイル）

	@param	None		： （$SCHEDULER_DATA/config/live配下のファイル）
	"""

	getdbinfo(dbg)

	path_1 = "%s/%s" % (os.getenv("Z4J_HOME"), "live")
	if dbg in ["1","2"]:
		print "Original File's PATH     = ",path_1

	path_2 = "%s/%s" % (os.getenv("SCHEDULER_DATA"), "config/live")
	if dbg in ["1","2"]:
		print "JobScheduler File's PATH = ",path_2

	check_jobfile(dbg)

	if dbg in ["1","2"]:
		print "===<<< Copy to Job & Job Chain Files or Remove >>>==="

	for dir in  env.job_dirs:
		if env.job_dirs[dir] == "ADD":
			cmd = "mkdir %s%s" % (path_2, dir)

			if dbg in ["1","2"]:
				print(cmd)

			with hide('running'):
				local(cmd)

	for file in  env.job_list:
		cmd = ''
		if env.job_list[file] == "DEL":
			cmd = "rm %s/%s" % (path_2, file)

		if env.job_list[file] in ["ADD","MOD"]:
			cmd = "cp -rp %s/%s %s/%s" % ( path_1, file[1:], path_2,  file[1:] )

		if cmd != '':
			if dbg in ["1","2"]:
				print(cmd)

			with hide('running'):
				local(cmd)

	for dir in  env.job_dirs:
		if env.job_dirs[dir] == "DEL":
			cmd = "rm -rf %s%s" % (path_2, dir)

			if dbg in ["1","2"]:
				print(cmd)

			with hide('running'):
				local(cmd)

#============================================================

def jos_set_last_id(last_id,dbg=0):
	"""
	jos_set_last_id
	DBにlast idを登録する
	@param	last_id		： DBに登録するタスクID情報

	@param	None		： （DBのjobid_tbl）
	"""

	connection = psycopg2.connect(
	 database = env.psqldatabase,
	 user = env.psqluser,
	 password = env.psqlpassword,
	 host = env.psqlhost,
	 port = env.psqlport)

	cur = connection.cursor()

	sql = """delete from jobid_tbl;"""
	cur.execute(sql)
	connection.commit()

	for jname in last_id:
		sql = """insert into jobid_tbl (job,lastid) values ('%s','%d');""" % (jname,last_id[jname])
		if dbg == "1":
			print sql
		cur.execute(sql)

	connection.commit()

	cur.close()
	connection.close()



#############################################################
# メインモジュール
#############################################################

#============================================================

def show_info(dbg=0):
	"""
	show_info
	JobSchedulerからジョブ情報を取得してzabbix_senderでZabbixにジョブの処理時間を送信する
	@param	None		： 

	@param	None		： 
	"""

	last_id={}

	getdbinfo(dbg)

	if dbg in ["1"]:
		print "===< show_info env.last_id Start >==="
		for jid in env.jos_last_id:
			print '  ',jid,' : ',env.jos_last_id[jid]
		print "===< show_info env.last_id End >==="

	for jname in env.jos_last_id:
		last_id[jname] = int(env.jos_last_id[jname],10)

	if dbg in ["1"]:
		print "===< show_info last_id Start >==="
		for jid in last_id:
			print '  ',jid,' : ',last_id[jid]
		print "===< show_info last_id End >==="

	jos_set_server(dbg)
	gethosts(dbg)
	check_jobfile()

	set_job_info(dbg)
	set_job_chain_info(dbg)

	if dbg in ["1"]:
		for serv in env.process_class:
			print "  %s : %s" % (serv,env.process_class[serv])

	root = jos_show_state(dbg)

	org_time = dt.strptime('1970-01-01 07:00:00','%Y-%m-%d %H:%M:%S')
	for e in root.findall('answer/state/jobs/job/'):	# ジョブの情報を取得
		for name,job in e.items():
			if name == 'path':
				if dbg in ["1"]:
					print 'job name : ',job

				flg = 0
				for jname in last_id:
					if jname == job:
						flg = 1
						break
				if flg == 0:
					last_id[job] = 1

				if dbg == '1':
					print "jos_show_history : %s : %d" % (job,last_id[job])

				root = jos_show_history(job,last_id[job], dbg)
				for elem in root.findall('answer/history/history.entry/'):
					exit_code = ''
					for n,t in elem.items():
						if n == 'start_time':
							start_time = dt.strptime(t, '%Y-%m-%dT%H:%M:%S.000Z')
							start_time_1 = int(time.mktime(time.strptime(t, '%Y-%m-%dT%H:%M:%S.000Z')))
						elif n == 'end_time':
							end_time = dt.strptime(t, '%Y-%m-%dT%H:%M:%S.000Z')
							end_time_1 = int(time.mktime(time.strptime(t, '%Y-%m-%dT%H:%M:%S.000Z')))
							end_time_2 = end_time_1 + 32400		# 9時間加算
						elif n == 'task':
							task = t
						elif n == 'exit_code':
							exit_code = t

					elapse = end_time_1 - start_time_1

								# Zabbixに情報を送信
					item = job.replace('/','.')
					item = item[1:]

					cmd ="echo -n -e '%s %s %s %s' | /usr/bin/zabbix_sender -z %s -T -i -" % ( env.process_class[job], item, end_time_2, elapse, env.zbx_server)
					local( cmd )

					if dbg in ["1"]:
						print '    ',task,' : ',exit_code,' :',start_time,' : ',end_time,' -> ',elapse
						print '                  end_time_2 = %s' % end_time_2
						print cmd

# 不要な機能のため、コメントアウト
#					if exit_code <> '':		# タスクIDを送信
#						item = "jos_server_status_%s" % (env.process_class[job])
#				##		exit_msg = '\\"Task ID %s : Exit %s\\"' % (task,exit_code)
#						exit_msg = '%s' % (exit_code)
#						cmd ="echo -n -e %s %s %s %s | /usr/bin/zabbix_sender -z %s -T -i -" % ( env.process_class[job], item, end_time_2, exit_msg, env.zbx_server)
#						local( cmd )
#
#						if dbg in ["1"]:
#							print cmd

					jid_flg = 0
					for jid in last_id:
						if jid == job:
							jid_flg = 1
							if last_id[jid] < int(task, 10):
								last_id[jid] = int(task, 10)

							break

					if jid_flg == 0:
						last_id[job] = int(task, 10)

	jos_set_last_id(last_id,dbg)

	if dbg in ["1"]:
		print "===< show_info last_id Start >==="
		for jid in last_id:
			print '  ',jid,' : ',last_id[jid]
		print "===< show_info last_id End >==="

#============================================================

def set_job_items(dbg=0):
	"""
	set_job_items
	Zabbixにジョブのitemを設定する
	@param	None		： 

	@param	None		： 
	"""

	getdbinfo(dbg)

	jos_set_server(dbg)
	gethosts(dbg)
	check_jobfile()

	set_job_info(dbg=0)
	set_job_chain_info(dbg=0)

	print "===<<< Set Items for Job >>>==="		# Jobのitemの処置
	for job in env.jos_job:
		name = job.replace('/','.')
		name = name.replace('.job.xml','')
		name = name[1:]
		hostid = env.zbx_server_list[env.process_class[job]]

		print '  %s --> %s(%s)' % (name,env.process_class[job],hostid)

		zbx_setitems(name,hostid,dbg)

	print "===<<< Set Items for Job Chain >>>==="	# Job Chainのitemの処置
	for job in env.jos_job_chain:
		name = job.replace('/','.')
		name = name.replace('.job_chain.xml','')
		name = name[1:]
		hostid = env.zbx_server_list[env.process_class[job]]

		print '  %s --> %s(%s)' % (name,env.process_class[job],hostid)

		zbx_setitems(name,hostid,dbg)

	print "===<<< Set Items for JOS Server >>>==="	# ジョブステータス用のitem登録
	for serv in env.zbx_server_list:
		hostid = env.zbx_server_list[serv]
		item = "jos_server_status_%s" % serv

		print '  %s --> %s(%s)' % (item,serv,hostid)

		zbx_setitems(item,hostid,dbg)
							# Trigger追加処理
		exp = "{%s:jos_server_status_%s.last()}#0" % (serv,serv)
		desp = "jos_server_status_localhost_event"
		zbx_settrigger(hostid,exp,desp,3,dbg)

	set_copy_jobs(dbg)				# 登録情報ファイルに現状ファイルを合わせる

#============================================================

def get_jobs(dbg=0):
	"""
	get_jobs
	Low Level Discavery用にジョブ情報をJSONで表示する
	@param	None		： 

	@param	None		： 
	"""

	getdbinfo(dbg)

	jos_set_server(dbg)
	gethosts(dbg)
	check_jobfile()

	set_job_info(dbg=0)
	set_job_chain_info(dbg=0)

	msg =''
	for job in env.jos_job:
		name = job.replace('/','.')
		name = name.replace('.job.xml','')
		name = name[1:]
		hostid = env.zbx_server_list[env.process_class[job]]

		msg = msg + '{"{#item_%s}":"%s"},' % (env.process_class[job],name)


	for job in env.jos_job_chain:
		name = job.replace('/','.')
		name = name.replace('.job_chain.xml','')
		name = name[1:]
		hostid = env.zbx_server_list[env.process_class[job]]

		msg = msg + '{"{#item_%s}":"%s"},' % (env.process_class[job],name)

	res = '{"data":[%s]}' %  msg[:-1]
	recvbuf = json.loads(res)

	print json.dumps(recvbuf, indent=4)

#============================================================

def trigger_switch(hostid,msg,rule,dbg=0):
	"""
	trigger_switch
	現状のTriggerを無効にして代わりを設定する
	@param	hostid		： 無効にするホストID
	@param	msg		： 無効にするトリガ名
	@param	rule		： 無効後に登録するトリガ条件

	@param	None		： 
	"""

	triggerid = gettriggerid(hostid,msg,dbg)
	gettrigger_disable(triggerid,dbg)

	desp = "%s" % "Switched by ZBX4JOS"
	zbx_settrigger(hostid,rule,desp,3,dbg)

	return

#============================================================

def trigger_ret(hostid,msg,dbg=0):
	"""
	trigger_switch
	trigger_switchで設定した内容を元に戻す
	@param	hostid		： 有効にするホストID
	@param	msg		： 元に戻すトリガ名

	@param	None		： 
	"""

	desp = "%s" % "Switched by ZBX4JOS"

	triggerid = gettriggerid(hostid,desp,dbg)
	zbx_deltrigger(triggerid,dbg)

	triggerid = gettriggerid(hostid,msg,dbg)
	gettrigger_enable(triggerid,dbg)

	return

#############################################################
# デバッグ、保守用モジュール
#############################################################

#============================================================

def getitems(hostid="10084",dbg=0):
	"""
	getitems
	item一覧を取得する
	@param	hostid		： 取得するアイテムのホストID

	@param	None		： 
	"""

	getdbinfo(dbg)

	recvbuf = zbx_getitems(hostid)
	recvkeys = recvbuf.keys()

	for k in recvkeys:
		if k == 'result':
			i = 0
			maxpoint = recvbuf[k]
			max = len(maxpoint)
			while i < max:
				results = recvbuf[k][i]
				reskeys = results.keys()
				print i," : ",results['itemid']," : ",results['name']," : ",results['key_']," : ",results['description']

				i = i + 1

#============================================================

def gettriggers(hostid="10084",dbg=0):
	"""
	getitems
	Trigger一覧を取得する
	@param	hostid		： 取得するトリガのホストID

	@param	None		： 
	"""

	getdbinfo(dbg)

	recvbuf = zbx_gettrigger(hostid,0)
	recvkeys = recvbuf.keys()

	for k in recvkeys:
		if k == 'result':
			i = 0
			maxpoint = recvbuf[k]
			max = len(maxpoint)
			while i < max:
				results = recvbuf[k][i]
				reskeys = results.keys()
				print i," : ",results['state']," : ",results['triggerid']," : ",results['expression']," : ",results['description']

				i = i + 1

#============================================================

def gethosts(dbg=0):
	"""
	getitems
	ホスト情報を取得し表示する
	@param	None		： 

	@param	None		： 
	"""

	getdbinfo(dbg)

	recvbuf = zbx_gethosts()

	recvkeys = recvbuf.keys()
	for k in recvkeys:
		if k == 'result':
			i = 0
			maxpoint = recvbuf[k]
			max = len(maxpoint)
			while i < max:
				results = recvbuf[k][i]
				reskeys = results.keys()
				env.zbx_server_list[results['host']] = results['hostid']
				if dbg in ["1"]:
					print i," : ",results['hostid']," : ",results['name']," : ",results['host']

				i = i + 1

#============================================================

def gethostid(hostname,dbg=0):
	"""
	getitemid
	ホスト情報を取得し表示する
	@param	hotname		： 取得するホスト名

	@param	None		： 
	"""

	getdbinfo(dbg)

	recvbuf = zbx_gethosts()

	recvkeys = recvbuf.keys()
	for k in recvkeys:
		if k == 'result':
			i = 0
			maxpoint = recvbuf[k]
			max = len(maxpoint)
			while i < max:
				results = recvbuf[k][i]
				reskeys = results.keys()
				env.zbx_server_list[results['host']] = results['hostid']
				if results['name'] == hostname:
					print results['hostid']

				i = i + 1

#============================================================
def createdb(dbg=0):
	"""
	getitems
	DBを作成する（初期化する)
	@param	None		： 

	@param	None		： 
	"""

	cmd = "dropdb %s" % env.psqldatabase
	local(cmd)
	cmd = "createdb %s" % env.psqldatabase
	local(cmd)

	connection = psycopg2.connect(
	 database = env.psqldatabase,
	 user = env.psqluser,
	 password = env.psqlpassword,
	 host = env.psqlhost,
	 port = env.psqlport)

	cur = connection.cursor()

	sql = """CREATE TABLE sysinfo (name text,value text);"""
	cur.execute(sql)
	connection.commit()

	sql = """CREATE TABLE jobid_tbl (job text,lastid text);"""
	cur.execute(sql)
	connection.commit()

	sql = "insert into sysinfo (name,value) values ('job_server','%s');" % env.jos_server
	cur.execute(sql)
	sql = "insert into sysinfo (name,value) values ('job_port','%s');" % env.jos_port
	cur.execute(sql)
	sql = "insert into sysinfo (name,value) values ('zbx_server','%s');" % env.zbx_server
	cur.execute(sql)
	sql = "insert into sysinfo (name,value) values ('zbx_login','%s');" % env.zbx_login
	cur.execute(sql)
	sql = "insert into sysinfo (name,value) values ('zbx_pass','%s');" % env.zbx_pass
	cur.execute(sql)
	sql = "insert into sysinfo (name,value) values ('jos_timeout','3');"
	cur.execute(sql)
	connection.commit()

	cur.close()
	connection.close()

###############################################################################
