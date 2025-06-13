[system] <- 'System being implemented'
[repo-name] <- 'Name of repo to be created and pushed to github'
[plan] <- 'Name of plan folder'
# Goal
Our goal is to create a high quality system for [system]. 

# Steps

## Review Guidelines, functional specifications, reference material 
Read contents of repo
First read folder guides, very important references. Keep detailed notes on these
- guides/deep-research-claude-agent-architecture.md
- guides/deep-research-system.md
- guides/repo-generation-guide.md
- multi-agent-claude-cli-research.md
- [include or exclude guides as relevant]

## Deep Research
Do deep research using perplexity mcp and firecrawler mcp

## Planning 
Based on research create detailed plan in folder [plan]_0 to build a comprehensive code repository for [system] with following features
- uses claude cli recursively , with mulitple parallel processes spawned, each with its own Claude CLI -based agent
- detailed docuentation for repo with documents folder
- detailed README
- readable, maintainable
- no file > 500 lines
- test driven development, London School TDD
- when more information needed, use deep reseaarch to expand knowledge




### baseline/prototype
Aim to create an initial baseline system that works end to end quickly. This will give early feedback and identify any big gaps in the plan. Getting to the baseline is the first target. 
run the baseline against benchmark. evaluate against the metrics. this is the baseline score. 

Further iterations should improve on the baseline score or at least not deteriorate unexpectedly ( as some iterations may not improve the metrics )


### benchmarks, metrics , evaluation system 
it is hard to assess a system without benchmarks 
it is critical to identify the right benchmark data set and metrics to evaluate the system. 
as part of the planning process, gather benchmark data, identify key metrics and an evaluation system. Get help from user if needed. or use deep research and find out. 


### architecture diagram. 
ARCHITECTURE.md - Every plan should have detailed ARCHITECTURE.md detaiing the system architecture and components
create detailed architecture diagram, zooming in on individual components and their integration in this file 
create nice mermaid diagrams, not the basic stupid ones                                                        │

### key modules and critical success factors
KEY_MODULES.md
Identify key modules and critical success factors. key modules are components which impact the outcome of the workflow the most. 
Example, in deep research, it could be generation of the right set of queries, scraping the top sites, summarizing properly when running out of context, writing the report properly, prompt quality quality of the memory system, quality of SPCT metrics, the skill level of the judge etc. identify them in order of importance and consider their optimality when building the system. 
Mention in above file key modules, critical success factors and justify how the architecture proposed will maximize these success factors 

### Risk factors
Identify key weaknesses of the proposed architure
What risks exist in the plan and proposed implementaiton. what assumptions have been made
what can go wrong 
is there scope creep. are  there complex systems being built 'blind' without incremental test based evaluation. Building complex systems directly without modularization and testing units is a recipe for failure. 


## Planning (contd )
- plan created in folder plan/1.md, 2.md , 3.md etc as logical sequential well planned coordinated steps
- each step tests comprehensively. creates tests runs tests
- create metrics to judge the plan quality using deepseek spct approach. after each planning round/revision, assess quality of the plan using above metrics. 

## Iterative planning
once initial plan is created, consider (a) benchmarks, metrics and evaluation system ( see below ) (b) key modules and critical success factors
think hard on the initial plan. how likely is it to succeed with the metrics on the benchmark. how well is it suited for the right module performance. is it set up to succeed on critical  success factors. 
Here is an opportunity to perform a revised deep search focused on these questions
Identify gaps and fill them, add more details, delete bad points , rewrite steps as necessary
Based on feedback above, improvde the inital plan and write to new folder [plan]_r1
Iterate on the intitial plan 2-3 times, 
Note that the plan is the structure. if that is done well, job is half done. well thought out plan eliminates hours to months of work. 
If plan finalized, rename folder [plan]_final 



Once planning done, start implementing 1.md, 2.md etc in the order. proceed only when all tests pass in each step. See details below. 

### Deliverables
- [plan]_0/
- [plan]_1/
- ..
- [plan]_final


## Implementation
- Build step by step. 
### Procedure
for i in range(1,n+1):
    1. Implement step i.md, along with test suite per TDD requirement.
    2. Run the tests. If bugs, fix them. Redo implementation if necessary based on state of bugs. If system is stuck, redo the implementation of the step from scratch, while keeping in mind the issues faced earlier. Log these issues to long term memory to avoid in future. 
    3. Create/edit examples folder. Create detailed user-friendly examples which user can run to understand the implementation. Run them. If there are issues running them, fix bugs, whether in example or source code, as appropriate
    4. Create/edit folder/file implementation/i.md with detailed documentation on the implementation per 1.md
    5. Create a file Functionally-Complete.md which explains what parts of the core functionality are actually complete from a user perspective ? What real actions can be taken at this point vs simulated , for example ? 
    5. Add, commit and push changes to github repo. Use github mcp. create new repo [repo-name] initially 

- if stuck, wait for user input . do this only if absolutely necessary. no more than 2-3 such stops during the entire process. 
- ask clarifying  questions to user up front rather than later 

### Deliverables
- [implementation]
- github push

## initial implementation in deep-research-claude. check in, push
## revised implementation #1 deep-research-claude. check in, push
## revised implementation #2 deep-research-claude, check in .push

