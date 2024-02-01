## Проект Foodgram

«Фудграм» — сайт, на котором пользователи публикуют рецепты, добавляют чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

Проект доступен по адресу https://foodgr.myftp.org/

## Стек:  
Django 3.2, Djoser, Python 3.11, DRF, PostgreSQL
## Как запустить проект  
Клонировать репозиторий и перейти в него в командной строке:  
`git clone url.git`  
  
### Cоздать и активировать виртуальное окружение:  
`python3 -m venv env`  
`source env/bin/activate`  
  
### Установить зависимости из файла requirements.txt:  
`python3 -m pip install --upgrade pip`  
`pip install -r requirements.txt`  
  
### Выполнить миграции:  
`python3 manage.py migrate`  
  
### При необходимости наполинить базу данных ингридиентами и тегами(:  
`python3 manage.py load_data`  
  
### Запустить проект:  
`python3 manage.py runserver`
## Примеры  
* Регистрация пользователя  
```  
POST /api/users/  
{
-   "email": "vpupkin@yandex.ru",
    
-   "username": "vasya.pupkin",
    
-   "first_name": "Вася",
    
-   "last_name": "Пупкин",
    
-   "password": "Qwerty123"
} 
```  
* Получение токена  
```  
POST /api/auth/token/login/  
{
-   "password": "string",
    
-   "email": "string"
} 
```  
* Получение списка произведений  
```  
GET /api/recipes/ 
{
-   "count": 123,
-   "next": "[http://foodgram.example.org/api/recipes/?page=4](http://foodgram.example.org/api/recipes/?page=4)",
-   "previous": "[http://foodgram.example.org/api/recipes/?page=2](http://foodgram.example.org/api/recipes/?page=2)",
-   "results": [
    -   {
        -   "id": 0,
        -   "tags": [
            -   {}
            ],
        -   "author": {
            -   "email": "user@example.com",
            -   "id": 0,
            -   "username": "string",
            -   "first_name": "Вася",
            -   "last_name": "Пупкин",
            -   "is_subscribed": false
            },
        -   "ingredients": [
            -   {
                -   "id": 0,
                -   "name": "Картофель отварной",
                -   "measurement_unit": "г",
                -   "amount": 1
                }
            ],
        -   "is_favorited": true,
        -   "is_in_shopping_cart": true,
        -   "name": "string",       
        -   "image": "[http://foodgram.example.org/media/recipes/images/image.jpeg](http://foodgram.example.org/media/recipes/images/image.jpeg)",
            
        -   "text": "string",
            
        -   "cooking_time": 1    
        }
    ]
}
```
Подробная документация по API проекта:   
api/docs/redoc.html