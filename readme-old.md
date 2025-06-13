# Goal
Our goal is to create a Roo code style system with
- specialized agents
- simple json based agent description and rule files for more detailed instructions
- comprehensive prompting blocks used and shared by all agents
- boomerang mode. orchestrator calls other agents, with enhanced instructions
- agents called by orchestrator are more focused. sometimes in their own sub folder 
- each agent finishes task and returns to orchestrator
- agents can optionally call other agents if set in configuration.
- coherent communication between agents

# Steps
Read contents of Roo-Code repo 

Then read folder guides, very important references. Keep detailed notes on these
- guides/deep-research-claude-agent-architecture.md
- guides/deep-research-system.md
- guides/repo-generation-guide.md
- multi-agent-claude-cli-research.md

Do deep research using perplexity mcp and firecrawler mcp
Based on research create detailed plan to build a comprehensive code repository for orchestrated recursive specialized multi-agentic systems
- uses claude cli recursively , with mulitple parallel processes spawned, each with its own Claude CLI -based agent
- detailed docuentation for repo with documents folder
- detailed README
- readable, maintainable
- no file > 500 lines
- test driven development, London School TDD
- when more information needed, use deep reseaarch to expand knowledge
- plan created in folder plan/1.md, 2.md , 3.md etc as logical sequential well planned coordinated steps
- each step tests comrpehensvily. creates tests runs tests
- build simpel, test , then expand 
- save versions  using github mcp. create new repo claude-roo
Then iterate on above plan 2-3 times, to identify gaps and fill them, add more details, delete bad points , rewrite steps as necessary
- once planning done, start implmeneting 1.md, 2.md etc in the order. proceed only when all tests pass in each step. 
- if stuck, wait for user input . do this only if absolutely necessary. no more than 2-3 such stops during the entire process. 
- ask clarifying  questions to user up front rather than later 



# Deliverable
## Comprehensive plan in folder plan
## Revised plan #1 in plan_revision_1
## Revised plan #2 in plan_revision_2
## Metrics to judge the repo using deepseek spct approach in plan_revision_2 

## First simple Implementation
This will be an early prototype, but fully functional, which has essential features but not too complex. claude-roo check in, push
## Sophisticated implementation #1
sophisticated implementation in claude-roo based on lessons from first implementaion above. check in, push
## revised sophisticated implementation #2 claude-roo check in, push
## revised sophisticated implementation #3 claude-roo check in .push

