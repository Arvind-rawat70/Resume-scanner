"""
Skill taxonomy: canonical name -> (category, [aliases]).

Shared by Module 1 (JD parsing) and Module 2 (resume parsing) so both sides
normalise skills to the same canonical names. Module 3 adds embeddings on top
so that skills NOT listed here (or phrased differently) still match semantically.
"""
from typing import Dict, List, Tuple

_RAW: Dict[str, Tuple[str, List[str]]] = {
    # Languages
    "Java": ("Language", ["java", "core java", "java 8", "java 11", "java 17", "j2ee"]),
    "Python": ("Language", ["python", "python3"]),
    "JavaScript": ("Language", ["javascript", "js", "es6", "ecmascript"]),
    "TypeScript": ("Language", ["typescript"]),
    "C#": ("Language", ["c#", "c sharp"]),
    "C++": ("Language", ["c++", "cpp"]),
    "Go": ("Language", ["golang", "go lang"]),
    "Kotlin": ("Language", ["kotlin"]),
    "PHP": ("Language", ["php"]),
    "Ruby": ("Language", ["ruby"]),
    "Scala": ("Language", ["scala"]),
    "SQL": ("Language", ["sql", "t-sql", "pl/sql", "plsql"]),
    # Backend frameworks
    "Spring Boot": ("Backend Framework", ["spring boot", "springboot"]),
    "Spring": ("Backend Framework", ["spring framework", "spring mvc", "spring"]),
    "Hibernate": ("Backend Framework", ["hibernate", "jpa"]),
    "Django": ("Backend Framework", ["django"]),
    "Flask": ("Backend Framework", ["flask"]),
    "FastAPI": ("Backend Framework", ["fastapi", "fast api"]),
    "Node.js": ("Backend Framework", ["node.js", "nodejs", "node js"]),
    "Express.js": ("Backend Framework", ["express.js", "expressjs"]),
    ".NET": ("Backend Framework", [".net", "dotnet", "asp.net", ".net core"]),
    "Microservices": ("Architecture", ["microservices", "microservice", "micro-services"]),
    "REST APIs": ("Architecture", ["rest api", "rest apis", "restful", "rest services", "restful apis"]),
    "GraphQL": ("Architecture", ["graphql"]),
    "System Design": ("Architecture", ["system design", "distributed systems", "scalable systems"]),
    # Frontend
    "React": ("Frontend", ["react", "react.js", "reactjs"]),
    "Angular": ("Frontend", ["angular", "angularjs"]),
    "Vue.js": ("Frontend", ["vue", "vue.js", "vuejs"]),
    "HTML/CSS": ("Frontend", ["html", "css", "html5", "css3", "sass", "scss"]),
    "Redux": ("Frontend", ["redux"]),
    "Next.js": ("Frontend", ["next.js", "nextjs"]),
    # Databases
    "PostgreSQL": ("Database", ["postgresql", "postgres"]),
    "MySQL": ("Database", ["mysql"]),
    "MongoDB": ("Database", ["mongodb", "mongo"]),
    "Oracle": ("Database", ["oracle db", "oracle database", "oracle"]),
    "SQL Server": ("Database", ["sql server", "mssql"]),
    "Redis": ("Database", ["redis"]),
    "Elasticsearch": ("Database", ["elasticsearch", "elastic search", "opensearch"]),
    "Cassandra": ("Database", ["cassandra"]),
    "DynamoDB": ("Database", ["dynamodb"]),
    # Messaging
    "Kafka": ("Messaging", ["kafka", "apache kafka"]),
    "RabbitMQ": ("Messaging", ["rabbitmq", "rabbit mq"]),
    # Cloud / DevOps
    "AWS": ("Cloud", ["aws", "amazon web services", "ec2", "s3", "lambda"]),
    "Azure": ("Cloud", ["azure", "microsoft azure"]),
    "GCP": ("Cloud", ["gcp", "google cloud", "google cloud platform"]),
    "Docker": ("DevOps", ["docker", "containers", "containerization"]),
    "Kubernetes": ("DevOps", ["kubernetes", "k8s"]),
    "CI/CD": ("DevOps", ["ci/cd", "ci cd", "continuous integration", "continuous delivery", "continuous deployment", "jenkins", "github actions", "gitlab ci"]),
    "Terraform": ("DevOps", ["terraform", "infrastructure as code", "iac"]),
    "Git": ("DevOps", ["git", "github", "bitbucket"]),
    "GitLab": ("DevOps", ["gitlab"]),
    "Jenkins": ("DevOps", ["jenkins"]),
    "Maven": ("DevOps", ["maven"]),
    "Gradle": ("DevOps", ["gradle"]),
    "Ansible": ("DevOps", ["ansible"]),
    "Helm": ("DevOps", ["helm"]),
    "Rancher": ("DevOps", ["rancher"]),
    "Linux": ("DevOps", ["linux", "unix", "bash", "shell scripting"]),
    # Monitoring / observability
    "Prometheus": ("Monitoring", ["prometheus"]),
    "Grafana": ("Monitoring", ["grafana"]),
    "ELK": ("Monitoring", ["elk", "elasticsearch", "elastic search", "logstash", "kibana"]),
    "Nagios": ("Monitoring", ["nagios"]),
    "Splunk": ("Monitoring", ["splunk"]),
    "New Relic": ("Monitoring", ["new relic", "newrelic"]),
    "AppDynamics": ("Monitoring", ["appdynamics"]),
    "PagerDuty": ("Monitoring", ["pagerduty"]),
    "Graylog": ("Monitoring", ["graylog"]),
    # Data / ML
    "Machine Learning": ("AI/ML", ["machine learning", "ml", "predictive modeling"]),
    "Deep Learning": ("AI/ML", ["deep learning", "neural networks"]),
    "NLP": ("AI/ML", ["nlp", "natural language processing", "text mining"]),
    "Sentence Transformers": ("AI/ML", ["sentence transformers", "sentence-transformers"]),
    "spaCy": ("AI/ML", ["spacy", "spa cy"]),
    "TensorFlow": ("AI/ML", ["tensorflow"]),
    "PyTorch": ("AI/ML", ["pytorch"]),
    "scikit-learn": ("AI/ML", ["scikit-learn", "sklearn", "scikit learn"]),
    "Pandas": ("Data", ["pandas"]),
    "NumPy": ("Data", ["numpy"]),
    "Spark": ("Data", ["apache spark", "pyspark", "spark"]),
    "Hadoop": ("Data", ["hadoop"]),
    "Data Analysis": ("Data", ["data analysis", "data analytics"]),
    "Power BI": ("Data", ["power bi", "powerbi"]),
    "Tableau": ("Data", ["tableau"]),
    "ETL": ("Data", ["etl", "data pipelines", "data pipeline"]),
    # Testing / process
    "JUnit": ("Testing", ["junit"]),
    "Unit Testing": ("Testing", ["unit testing", "unit tests", "tdd", "test driven development"]),
    "Selenium": ("Testing", ["selenium"]),
    "Agile": ("Process", ["agile", "scrum", "kanban"]),
    "JIRA": ("Process", ["jira"]),
}

# canonical -> category
CATEGORY: Dict[str, str] = {k: v[0] for k, v in _RAW.items()}

# alias (lowercase) -> canonical. Longest aliases are matched first by the parser.
ALIAS_TO_CANONICAL: Dict[str, str] = {}
for canonical, (_, aliases) in _RAW.items():
    ALIAS_TO_CANONICAL[canonical.lower()] = canonical
    for a in aliases:
        ALIAS_TO_CANONICAL[a.lower()] = canonical

# If a more specific skill is found, drop the generic one it contains
# (e.g. "Spring Boot" present -> don't also report bare "Spring" from the same phrase).
SUBSUMES = {"Spring Boot": {"Spring"}, "Node.js": {"Express.js"}}

SOFT_SKILLS = {
    "Communication": ["communication", "communicate", "written and verbal"],
    "Teamwork": ["teamwork", "team player", "collaborat", "cross-functional"],
    "Leadership": ["leadership", "mentor", "lead a team", "team lead"],
    "Problem Solving": ["problem solving", "problem-solving", "analytical", "troubleshoot"],
    "Ownership": ["ownership", "self-motivated", "self motivated", "proactive", "initiative"],
    "Adaptability": ["adaptab", "fast-paced", "fast paced", "learn quickly", "quick learner"],
    "Time Management": ["time management", "prioritiz", "deadline"],
}
