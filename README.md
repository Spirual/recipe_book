## Проект Recipe Book

Мною полностью разработан бекенд проекта. Моя работа включала создание эффективной серверной части, обеспечивающей взаимодействие с уже готовым фронтендом. Приложил усилия к созданию надежного и оптимизированного бекенда, обеспечивая бесперебойную работу всей системы.

Проект «Книга рецептов» — сайт, на котором пользователи публикуют рецепты, добавляют чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Стек:  
Django 3.2, Djoser, Python 3.11, DRF, PostgreSQL, GitHub, GitHub Actions
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
  
### При необходимости наполнить базу данных ингредиентами и тегами(:  
`python3 manage.py load_data`  
  
### Запустить проект:  
`python3 manage.py runserver`

### Развернуть проект на удаленном сервере:

-   Выполните вход на свой удаленный сервер
    
-   Установите docker на сервер:
    Поочерёдно выполните на сервере команды для установки Docker и Docker Compose для Linux. Наберитесь терпения: установка займёт некоторое время.

```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin
```
-   На сервере отредактируйте файл nginx.conf 
```
sudo nano /etc/nginx/sites-enabled/default
```
и в строке server впишите ваш доменный адрес и ip
```
server { ...  <ваш-ip> <ваш-домен>; ... }
```
и не забудьте проверить и перезагрузить конфиг файл
```
sudo nginx -t
sudo systemctl reload nginx
```
-   На сервере создайте директории foodgram/infra и создайте там .env файл и впишите значения для переменных:
   ```
	POSTGRES_USER=  
	POSTGRES_PASSWORD=  
	POSTGRES_DB=  
	POSTGRES_HOST=  
	POSTGRES_PORT=  
	SECRET_KEY=
	DJANGO_DEBUG= 
	DJANGO_ALLOWED_HOSTS=
```
    
-  Проект настроен на автоматизацию деплоя с GitHub Actions. Деплой происходит при push на сервер GitHub в ветку master. Для работы с Workflow добавьте в Secrets GitHub переменные окружения для работы:
```
	DOCKER_PASSWORD=<пароль от DockerHub>
	DOCKER_USERNAME=<имя пользователя>

	USER=<username для подключения к серверу>
	HOST=<IP сервера>
	PASSPHRASE=<пароль для сервера, если он установлен>
	SSH_KEY=<ваш SSH ключ (для получения команда: cat ~/.ssh/id_rsa)>

	TELEGRAM_TO=<ID чата, в который придет сообщение>
	TELEGRAM_TOKEN=<токен вашего бота>
```
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
* Получение списка рецептов  
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

## Автор:

- [Владимир Фатеев](https://github.com/Spirual/) 
