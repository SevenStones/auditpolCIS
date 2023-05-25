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

The automated assessment results from AuditpolCIS, as it's based on CIS Benchmarks, helps in the support of meeting audit requirements for a number of programs, not least PCI-DSS: 

  - Audit account logon events: Helps in monitoring and logging all attempts to authenticate user credentials (PCI-DSS Requirement 10.2.4).
  - Audit object access: Monitors access to objects like files, folders, and registry keys that store cardholder data (PCI-DSS Requirement 10.2.1).
  - Audit privilege use: Logs any event where a user exercises a user right or privilege (PCI-DSS Requirement 10.2.2)

Note that the script also generates output relevant to other audit/compliance/regulatory requirements to do with the retention of events data. 
Local log files sizes and retention policies are useful in assessing compliance with e.g. PCI-DSS 4 5.3.4 and 10.5.1 requirements. 

![image](https://user-images.githubusercontent.com/1404877/232906246-0feec791-7395-4196-9437-ce243b5a9361.png)

Further details on usage and other background info is at https://www.seven-stones.biz/blog/auditpolcis-automating-windows-siem-cis-benchmarks-testing/
