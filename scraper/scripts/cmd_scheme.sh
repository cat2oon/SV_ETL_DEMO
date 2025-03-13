# --------------------------------------------------------------------------------
# NOTE: 
# - 사용할 ooo.json 파일의 디렉터리에서 아래 명령어 실행
# - confluentinc/cp-schema-registry 이미지에 kafka-avro-console-consumer 명령 제공
# - AvroProducerd를 통해 자동 등록되어 이 스크립트는 필요 없어짐
# --------------------------------------------------------------------------------

# schema registry variables
schema_host="http://172.18.0.13:8081"  
header="Content-Type:application/vnd.schemaregistry.v1+json"

# item control variables
query_id=1
topic="marketplace.joongonara.product.scraped"
subject="${topic}-key" # # "${topic}-value"

# add schema 
# curl -X POST ${schema_host}/subjects/${subject}/versions -H ${header} --data '{"schema":"{\"type\":\"record\",\"name\":\"ProductAddRequest\",\"fields\":[{\"name\":\"pid\",\"type\":\"int\"}, {\"name\": \"price\", \"type\": \"int\"}, {\"name\": \"title\", \"type\": \"string\"}, {\"name\": \"description\", \"type\": \"string\"}, {\"name\": \"condition\", \"type\": \"string\"},{\"name\": \"category_path\", \"type\": \"string\", \"default\": \"\" }, {\"name\": \"error_cause\", \"type\": \"string\", \"default\": \"\" }, {\"name\": \"scraped_at\", \"type\": \"string\"}]}"}'

# update schema 
# curl -X POST ${schema_host}/subjects/${subject}/versions -H ${header} --data @product_schema.json 

# delete shceme  
version=2
# curl -X DELETE ${schema_host}/subjects/${subject}/versions/${version}

# query schema version 
# curl -X GET ${schema_host}/subjects/${subject}/versions/

# check registery schema all list
# curl -X GET ${schema_host}/subjects

# query schema by id
# curl -X GET ${schema_host}/schemas/ids/${query_id} | jq

# set compatibility for specific subject
# curl -X PUT ${schema_host}/config/${subect} -H ${header} --data '{"compatibility": "NONE"}' 