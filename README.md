# auditpolCIS
CIS Benchmark testing of Windows SIEM configuration

This is an application for testing the configuration of Windows Audit Policy settings against the CIS Benchmark recommended settings. A few points:

- The tested system was Windows Server 2019, and the benchmark used was also Windows Server 2019.
- The script connects with SSH. SSH is included with Windows Server 2019, it just has to be enabled. If you would like to see WinRM (or other) 
connection types, let me know or send a PR.
- Some tests are included here which were not included in the CIS guide. The recommended settings for these Subcategories are based on the logging volume
for these events, versus the security value. In nearly all cases, the recommendation is to turn off auditing for these settings. 
- The YAML file cis-benchmarks.yaml is the YAML representation of the CIS Benchmark guideline for each Subcategory.
- The command run under SSH is auditpol /get /category:*

![image](https://user-images.githubusercontent.com/1404877/232906246-0feec791-7395-4196-9437-ce243b5a9361.png)

