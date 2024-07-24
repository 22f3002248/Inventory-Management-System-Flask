import requests
import json

base = 'http://127.0.0.1:5000/'

item_get = requests.get(base+'api/item/1')
print(json.dumps(item_get.json(), indent=2))

# item_put = requests.put(base+'/api/item/1', json={
#     'name': 'Api_Item',
#     'partno': 'API123',
#     'category': 1,
#     'description': 'Api item descriptio changed !',
#     'quantity': 111,
#     'price': 1111.0,
# })
# print(json.dumps(item_put.json(), indent=2))

# item_delete = requests.delete(base+'/api/item/2')
# print(json.dumps(item_delete.json(), indent=2))

# item_list_get = requests.get(base+'/api/item/list')
# print(json.dumps(item_list_get.json(), indent=2))

# item_list_post = requests.post(base+'/api/item/list', json={
#     'name': 'Api_Item_POST',
#     'partno': 'APIPOST',
#     'category': 2,
#     'description': 'Api item descriptio changed !_POST',
#     'quantity': 222,
#     'price': 2222.0,
# })
# print(json.dumps(item_list_post.json(), indent=2))
