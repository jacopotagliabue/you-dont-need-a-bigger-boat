Welcome to your new dbt project!

### Using the starter project

Try running the following commands:
- dbt run
- dbt test


### Resources:
- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers
- Join the [chat](http://slack.getdbt.com/) on Slack for live discussions and support
- Find [dbt events](https://events.getdbt.com) near you
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices

### Configuration for ~/.dbt/profiles.yml

This configuration should be used in your profiles.yml to configure access to snowflake. 
dbt will load secrets from this local file when launching a step. The profiles are maped to models
in the dbt_project.yml.

    default:
        outputs:
            events:
              type: snowflake
              threads: 1
              user: 
              password: 
              database: 
              account: 
              role: 
              warehouse: 
              schema:  #Use the source schema here.
        
            public:
              type: snowflake
              threads: 1
              user: 
              password: 
              database: 
              account: 
              role: 
              warehouse: 
              schema: #Use the public schema here.

    target: events 

