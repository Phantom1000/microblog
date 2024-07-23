docker run --name elasticsearch -d --rm --net elastic -p 9200:9200 --memory="2GB" -e discovery.type=single-node -e xpack.security.enabled=false -t elasticsearch:8.14.1

elasticsearch:
    image: elasticsearch:7.17.22
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    mem_limit: 2GB


docker run -d --name my-redis-stack -p 6379:6379  redis/redis-stack-server:latest

docker exec -it my-redis-stack sh

docker run -d --name my-redis-stack -p 6379:6379 -v /Users/my-redis/:/data -e REDIS_ARGS="--requirepass your_password_here --appendonly yes" redis/redis-stack-server:latest

docker run --name mysql -d -e MYSQL_RANDOM_ROOT_PASSWORD=yes \
    -e MYSQL_DATABASE=microblog -e MYSQL_USER=microblog \
    -e MYSQL_PASSWORD=<database-password> \
    --network microblog-network \
    mysql:latest

docker run --name microblog -d -p 8000:5000 --rm -e SECRET_KEY=my-secret-key \
    -e MAIL_SERVER=smtp.googlemail.com -e MAIL_PORT=587 -e MAIL_USE_TLS=true \
    -e MAIL_USERNAME=your-gmail-username -e MAIL_PASSWORD=your-gmail-password \
    --network microblog-network \
    -e DATABASE_URL=mysql+pymysql://microblog:database-password@mysql/microblog \
    microblog:latest
#Проверьте ls -ld /Users/my-redis/права доступа к каталогу на хост-компьютере.
#
#Таким образом, если включена функция сохранения, данные сохраняются в томе  /data, который можно использовать с  --volumes-from some-volume-container или -v /docker/host/dir:/data