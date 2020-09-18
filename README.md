# announcements_service


simple announcements API

GET `/announcements/1`

```json
{
    "title": "....A ... A    shark :)",
    "id": 1,
    "publishedAt": "2020-09-18T16:31:20Z",
    "weight": 1,
    "imgUrl": "",
    "url": "",
    "description": "some description",
    "expireTime": "2020-09-26T16:31:20H",
    "nextId": 2,
    "lastId": null
}
```

GET `/announcements/all`
GET `/announcements/` for all

```json
{
  "data":{
    "title": "....A ... A    shark :)",
    "id": 1,
    "publishedAt": "2020-09-18T16:31:20Z",
    "weight": 1,
    "imgUrl": "",
    "url": "",
    "description": "some description",
    "expireTime": "2020-09-26T16:31:20H",
    "nextId": 2,
    "lastId": null
	}
}
```



## TODO

- [ ] tag (/get/tag/list)
- [ ] Admin ( set on docker)
- [ ] Editor or Reviewer (set by admin and save on redis)
- [ ] user submit and review service
- [ ] easy to complete custom auth (default: Google Oauth)





