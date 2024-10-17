# DQG
go 1.23


docker run -dit -p 8002:8002 -v $(pwd)/outputs:/app/outputs --name dqg-container maziar/dqg:latest
