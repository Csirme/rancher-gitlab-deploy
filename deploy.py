import requests
import json

api = "%s://%s/v3" % ("https", "rancher.rrt-inc.com")
session = requests.Session()
session.auth = ("token-kk9df", "67ldbsbr55n47qxzhcchgnxkhdhkzh5hxz8hztnpztts97d2tdrxrq")
upgrade_url = "%s/%s" % (api,"project/c-dhq25:p-zv8sq/workloads/deployment:rrt-srm-eureka:erueka")
pr = session.get(upgrade_url)
upgrade_data = pr.json()
upgrade_data['containers'][0]['image']="hub.rrt-inc.com/eureka:531c4569"
headers = {'Content-Type': 'application/json'}
upgrade_containers = {'containers':upgrade_data['containers']}
ur = session.put(upgrade_url,headers=headers,data=json.dumps(upgrade_containers))
print(ur)
