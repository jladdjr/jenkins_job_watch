# jenkins_job_watch

## Requirements

`pip install -U -r requirements.txt`

## Sample Usage

```
jenkins_job_watch.py --build 100 --sorted

Getting results for:
http://jenkins/job/My_Integration_Test/100/
My test run description
2020-11-11

Failures:
  1   test_bar
  2   test_baz
  3   test_foo
```

## Configuration

In the local directory or your home directory, create `.jenkins_job_watch`:

```
---
jenkins_host: http://jenkins-host
username: joe_user@email.com
token: <jenkins api token>

job: My_Integration_Test
```
