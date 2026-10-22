# 本地 RAG 知识库 × Dify
**Local Retrieval API with Ollama, BGE-M3 and Chroma**

把本地 PDF、Excel 转成可检索的知识片段，通过 FastAPI 提供搜索接口，并接入 Dify 的外部知识库。

这是一个**文档入库与向量检索示例**：本仓库负责返回相关片段，回答生成由 Dify 或其他调用方完成，不需要在这里部署聊天大模型。

[快速开始](#快速开始) · [调用接口](#调用接口) · [接入 Dify](#接入-dify) · [当前边界](#当前边界)

## 工作原理

~~~mermaid
flowchart LR
    A["PDF / Excel"] --> B["加载与分块"]
    B --> C["Ollama BGE-M3"]
    C --> D["本地 Chroma"]
    E["查询文本"] --> F["FastAPI"]
    F <--> D
    F --> G["搜索页面 / Dify"]
~~~

- 文档按 512 字符分块，重叠 64 字符。
- BGE-M3 通过本机 Ollama 接口生成向量。
- Chroma 将向量持久化到 chroma_db/。
- /search 用于直接检索；/retrieval 返回 Dify 所需的 records 格式。

## 快速开始

建议使用 **Python 3.11** 和独立虚拟环境。仓库沿用 Chroma 0.4.22 的历史依赖组合，避免直接使用系统 Python 或 NumPy 2 环境。

### 1. 安装依赖

~~~bash
git clone https://github.com/sunShineLoveMe/local-rag-bge3-chroma-dify.git
cd local-rag-bge3-chroma-dify

python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt "numpy<2" pypdf
~~~

PDF 加载器使用 pypdf；它与 requirements.txt 中列出的 PyPDF2 是不同的包，因此上面的命令显式补装 pypdf。Excel 解析使用 Unstructured。

### 2. 准备 Ollama 嵌入模型

先安装并启动 Ollama；尚未运行服务时，可在另一个终端执行 ollama serve。

~~~bash
ollama pull bge-m3
curl -fsS http://127.0.0.1:11434/api/tags
~~~

首次 pull 会下载模型。代码默认使用 **bge-m3:latest** 和 **http://localhost:11434**，修改入口在 [embeddings.py](embeddings.py)。

### 3. 放入文档并入库

将至少一份 PDF、.xlsx 或 .xls 文件放入 data/。该目录只保留待导入文档；移除仓库自带的空占位文件，避免导入脚本将它识别为不支持的格式：

~~~bash
rm -f data/.gitkeep
python ingest.py
~~~

第一次体验建议使用可复制文本的小型 PDF。重复运行 ingest.py 会继续追加片段，当前没有文件去重或增量更新机制。

### 4. 启动 API

~~~bash
python -m uvicorn main:app --host 127.0.0.1 --port 8001
~~~

打开：

- **http://127.0.0.1:8001/**：内置搜索与 Dify 接口测试页面。
- **http://127.0.0.1:8001/docs**：FastAPI 交互文档。

所有 Python 命令均在项目根目录执行，入库和服务才能使用同一个 chroma_db/。

## 调用接口

### 直接搜索

~~~bash
curl -G 'http://127.0.0.1:8001/search' \
  --data-urlencode 'query=这里填写文档中能回答的问题' \
  --data-urlencode 'k=3'
~~~

响应包含 results，每条结果有 content 和 score。score 来自 Chroma 的原始检索分数，不是已经归一化的相关性百分比。

### Dify 格式检索

~~~bash
curl -X POST 'http://127.0.0.1:8001/retrieval' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer local-demo-only' \
  -d '{
    "knowledge_id": "local-docs",
    "query": "这里填写文档中能回答的问题",
    "retrieval_setting": {
      "top_k": 3,
      "score_threshold": 0
    }
  }'
~~~

当前只检查 Authorization 的 Bearer 格式，**并未校验密钥值**；示例中的值仅用于本地调试。knowledge_id 目前也不隔离不同知识库，查询仍使用同一个 Chroma 存储。

## 接入 Dify

1. 在 Dify 中添加外部知识库 API，API Endpoint 填 **http://127.0.0.1:8001**。Dify 会自动追加 /retrieval，不要在基础地址中重复填写该路径；见 [Dify 官方接入说明](https://github.com/langgenius/dify-docs/blob/main/en/self-host/use-dify/knowledge/connect-external-knowledge-base.mdx)。
2. 本地调试时填写一个非空 API Key，并连接 knowledge_id 为 local-docs 的外部知识库。
3. 使用与 /search 相同的问题，核对返回片段和来源，再接入问答流程。

**地址必须从 Dify 所在环境可达。** 如果 Dify 在 Docker 中，127.0.0.1 指向容器自身；需要配置可访问的宿主机地址。不要将当前未完成密钥验证的检索服务直接开放到公网。

## 当前边界

- 主要处理文本 PDF 与 Excel；扫描 PDF 没有内置 OCR 流程。
- data/ 默认没有可用业务文档，启动服务不会自动导入数据。
- /retrieval 当前按 score >= score_threshold 过滤，而 Chroma 返回的距离通常越小越近；阈值逻辑需校准，不能把 0.5 解读为“50% 相关”。建议先用 /search 检查召回。
- 依赖未完整锁定，首次部署需要验证本机的 LangChain / Chroma / NumPy 组合。

## 目录与评估

| 文件或目录 | 用途 |
| --- | --- |
| embeddings.py | Ollama 嵌入接口 |
| ingest.py | 文档加载、分块与入库 |
| main.py | FastAPI、搜索和 Dify 接口 |
| data/ | 待导入文档 |
| chroma_db/ | 本地向量存储 |
| test_case_dataset/ | 召回评估脚本与问题集 |

服务运行且已导入对应材料后，可执行：

~~~bash
python test_case_dataset/auto_recall_eval.py
~~~

评估脚本针对仓库中的固定问题集；更换知识材料后，应同步调整问题和黄金答案，结果才有参考意义。

当前仓库未提供独立 LICENSE 文件；复用或分发前请与维护者确认授权范围。
