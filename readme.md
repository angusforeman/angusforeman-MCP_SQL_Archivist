# SQL Archivist
Research spike exploring the efficacy of using an MCP Server to encapsulate access to an Archive of content represented by A) SQL data B) unstructured data and C) simple business rules

# Running the LLM with MCP to interogate the archive
Follow the steps below if recreating the environment or building the DB from scratch
```bash
uv run python azureopenai_mcp_chat.py
``` 
### Sample queries
```In the chat
>Is the DuPrez Audio Archive healthy?
>>this should return a count of ~150

>is a recording of "the birds" in the archive?
>>this should return a positive response

>are the series of the birds quorom?"
>>this should activate a business rules lookup to qualify what qurom means

>yes (there is no auto-turn, so you need to give the LLM a chance to apply the rules via SQL)
>> Should confirm is the recordings are quorum

>How many recordings of A history of the world in 100 objects are there?
>>This will likely return 0 as the 100 programmes are actually listed by episode titles, an real world challenge with indexing of real world content

>Try checking other likely fields in the archive for these episodes  
>>This should find the recordings by searching under album or artists fields
```
### Concepts in the MCP Server
- healthcheck
- SQL query
- Schema query
- Glossary
- Business rules
- Overview 

### ligging tools direct to console
NOTE: The  logging of the MCP server in the console can be suppressed via the .env file MCP_SERVER_PARAMS=--quiet


# Runtime setup
```bash
uv add duckdb
uv addd mcp[cli]
```
# Azure resource setup
Set up Azure OpenAI Chat GPT5 instance 
update .env file based on the template and the Azure servive details
you can use the default LLM and MCPserver details
``

# create new archiveDB and reimport of sample data
will be necessary if pulling fresh from repo
```bash
cd archivedb
uv run python create_archivedb.py #create table structure & indexes
uv run python import_to_archive.pt archive_metadata-examplefile.jsonl ## using --drop will clear any existing content
uv run python ./run_archivedb_query.py "select count(*) from audio_files" # validate record count
```