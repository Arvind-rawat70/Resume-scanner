import pathlib
from app.services.jd_parser import find_skills, parse_job_description

SAMPLE = pathlib.Path(__file__).parents[2] / "sample_data" / "jd_java_backend.txt"


def names(jd, importance):
    return {s.name for s in jd.skills if s.importance == importance}


def test_word_boundaries():
    assert find_skills("We use JavaScript daily") == ["JavaScript"]       # not Java
    assert find_skills("PostgreSQL and MySQL") == ["PostgreSQL", "MySQL"]  # not SQL
    assert "C++" in find_skills("Strong C++ and C# skills")
    assert find_skills("Spring Boot services") == ["Spring Boot"]          # not also Spring
    assert find_skills("we will express interest and rest") == []


def test_full_jd():
    jd = parse_job_description(SAMPLE.read_text())
    assert jd.title == "Senior Java Backend Developer"
    assert {"Java", "Spring Boot", "PostgreSQL", "SQL", "Microservices", "REST APIs",
            "JUnit", "Docker", "CI/CD"} <= names(jd, "required")
    assert {"Kafka", "RabbitMQ", "AWS", "Kubernetes"} <= names(jd, "preferred")
    # "About us" mentions AWS/Kubernetes but that section is ignored; not promoted to required
    assert "AWS" not in names(jd, "required")
    assert jd.experience.min_years == 5
    assert jd.experience.seniority == "Senior"
    levels = {e.level: e for e in jd.education}
    assert levels["Bachelor's"].required and "Computer Science" in levels["Bachelor's"].fields
    assert not levels["Master's"].required
    assert any("AWS Certified" in c for c in jd.certifications)
    assert len(jd.responsibilities) == 5
    assert {"Communication", "Problem Solving"} <= set(jd.soft_skills)


def test_experience_ranges_and_specific_vs_general():
    jd = parse_job_description(
        "Data Engineer\nRequirements\n- 3-5 years of experience in data engineering\n"
        "- 2+ years of experience with Spark\n" + "x " * 20)
    assert (jd.experience.min_years, jd.experience.max_years) == (3, 5)


def test_unstructured_paragraph():
    jd = parse_job_description(
        "We're hiring a Python developer with minimum 3 years of experience. "
        "You should know Django, FastAPI and PostgreSQL. Docker is a plus.")
    assert names(jd, "required") >= {"Python", "Django", "FastAPI", "PostgreSQL"}
    assert names(jd, "preferred") == {"Docker"}
    assert jd.experience.min_years == 3


def test_missing_experience_defaults_to_fresher():
    jd = parse_job_description(
        "We are looking for a backend engineer with strong Java and SQL skills. "
        "You should be comfortable with REST APIs and debugging production issues."
    )
    assert jd.experience.min_years is None
    assert jd.experience.seniority == "Fresher"


def test_preferred_stack_intro_and_bullets_are_not_required():
    jd = parse_job_description(
        "Candidates can choose their own technology stack, but the following is preferred:\n"
        "- Frontend: React.js\n"
        "- Backend: Python / FastAPI\n"
        "- AI/NLP: Sentence Transformers, spaCy or equivalent\n"
        "- Database: PostgreSQL / MongoDB"
    )
    assert {"React", "Python", "FastAPI", "Sentence Transformers", "spaCy", "PostgreSQL", "MongoDB"} <= {s.name for s in jd.skills if s.importance == "preferred"}
    assert {"React", "Python", "FastAPI", "Sentence Transformers", "spaCy", "PostgreSQL", "MongoDB"}.isdisjoint({s.name for s in jd.skills if s.importance == "required"})


def test_compact_key_skills_line_extracts_all_known_skills():
    jd = parse_job_description(
        "Key Skills\n"
        "Java Node.jsAWSMicroservicesMicrosoft AzureGCPSpring BootReact.jsJavascriptAngularTypeScriptCI/CDRestGITJenkinsMavenGradleDockerGitlabKubernetesTerraformAnsibleHelmPythonPrometheusGrafanaElkNAGIOSSplunkNew RelicAppdynamicsPagerdutyRancherGraylog"
    )
    required = {s.name for s in jd.skills if s.importance == "required"}
    assert {"Java", "Node.js", "Microservices", "Azure", "GCP", "Spring Boot", "React", "JavaScript",
            "Angular", "TypeScript", "CI/CD", "Docker", "Kubernetes", "Terraform", "Python",
            "Jenkins", "Maven", "Gradle", "GitLab", "Ansible", "Helm", "Prometheus", "Grafana",
            "ELK", "Nagios", "Splunk", "New Relic", "AppDynamics", "PagerDuty", "Rancher", "Graylog"} <= required


def test_semantic_match_score_rewards_similar_technical_text():
    from app.services.semantic_match import semantic_similarity

    jd = "We are looking for a Python FastAPI backend engineer with PostgreSQL and React experience."
    resume = "Experienced backend developer with Python, FastAPI, PostgreSQL and React for production applications."
    score = semantic_similarity(jd, resume)
    assert score >= 0.7
