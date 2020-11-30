# 客製化貼文 API

[EN? (None)]()

[Docs](https://github.page.taki.dog/announcements_service/swagger_api.html)

提供**簡單**可自定格式與簡單審查服務的API，使用Redis做資料儲存。

並且支援貼文標籤，標籤查詢等功能。

大致可以獲的的貼文內容：

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

目前僅有開發版本。

## release setup

....  

## develop setup

1. 安裝好`redis-server`

   如果皆採用預設並在local架設Redis，並不需要特別指定Redis URL

   如有自行更動port，或是使用外部Redis

   ```bash
   export REDIS_URL=redis://127.0.0.1:6379
   ```


2. 安裝python 第三方套件

   ```bash
   cd src
   pip3 install -r requirements.txt
   ```

3. 執行

   ```bash
   # on src 
   gunicorn -c gunicorn_config.py web_server:app
   ```

   
## 功能修改

### Auth

在預設條件下的註冊，密碼僅支援50~80位，推薦使用`SHA-256`

採用JWT的驗證方式，如果有要客製化可以參考`src/auth/auth.py` and `src/view/auth_view.py`

### Posts field

可以在`src/utils/config.py`中`ANNOUNCEMENT_FIELD`進行欄位修正

目前強制使用的欄位`publishedAt` `expireTime` `applicant` `tag` `id`

其餘欄位可以做修改



## TODO

- [ ] Oauth
- [ ] Docker
- [x] API Docs
- [ ] requirements.txt 






