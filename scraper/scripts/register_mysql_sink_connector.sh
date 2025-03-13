# --------------------------------------------------------------------------------
# NOTE: 
# - (주의) 사용할 ooo.json 파일의 디렉터리에서 아래 명령어 실행
# - https://docs.confluent.io/platform/current/connect/references/restapi.html
# --------------------------------------------------------------------------------
header="Content-Type: application/json"
connector_name="mysql-sink-connector"
connect_host="http://172.18.0.10:8083"

# mysql sink connector 등록
# curl -X POST -H "${header}" --data @mysql_sink.json ${connect_host}/connectors

# mysql sink connector 삭제
# curl -X DELETE ${connect_host}/connectors/${connector_name}

# 등록된 connector 확인
# curl -X GET "${connect_host}/connectors/" 
curl -X GET ${connect_host}/connectors/${connector_name}/config
# curl -X GET ${connect_host}/connectors/${connector_name}/status
# curl -X POST ${connect_host}/connectors/${connector_name}/restart

# task_id=0
# curl -X GET ${connect_host}/connectors/${connector_name}/tasks/${task_id}/status

# 커넥트 설정 업데이트
# curl -X PATCH -H ${header} --data @patch.json "${connect_host}/connectors/${connector_name}/config"


# --------------------------------------------------------------------------------
# MySQL 체크
# --------------------------------------------------------------------------------
docker_container_name="mysql"
mysql_user="sv_user"
mysql_password="sv_demo"
mysql_database="joongo_market_product_db"

# 테스트 쿼리
# query="SELECT * FROM my_table LIMIT 10;"
query="SELECT TABLE_NAME, TABLE_ROWS, CREATE_TIME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '${mysql_database}'";

# 쿼리 실행
# docker exec -i $docker_container_name mysql -u $mysql_user -p $mysql_password -D $mysql_database -e "${query}"