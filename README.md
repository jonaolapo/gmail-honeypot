Gmail Honeypot Infrastructure
=============================
**Authors:** Jeremiah Onaolapo, Enrico Mariconti, and Gianluca Stringhini (2016).

This is the infrastructure we developed to instrument and monitor honey accounts, as presented in the paper below. If you use the infrastructure in your work, please cite or acknowledge us (_bib_ entry follows).

```text
@inproceedings{onaolapo:2016:gmailhoneypot,
  title={What Happens After You Are Pwnd: Understanding the Use of Leaked Webmail Credentials in the Wild},
  author={Onaolapo, Jeremiah and Mariconti, Enrico and Stringhini, Gianluca},
  booktitle={ACM SIGCOMM Internet Measurement Conference (IMC)},
  year={2016},
  organization={Association for Computing Machinery (ACM)}
}
```

Below is a description of the files and subdirectories in the **general** directory. 


Files
=====

* **metadata.conf** - This file stores configuration details. Edit this file to specify paths to data files and other required values for your experiment.

* **SMTPserver_ext.py** - This is the sinkhole SMTP server. It receives emails and writes them to disk without forwarding them to the intended destination.

* **popper.py** - POP mail client that retrieves notifications from the notification store (sent by honey accounts).

* **scraper.py** - Connects to honey accounts to download pages that contain information about accesses.

* **p.1_build_batch_oracle.py** - Builds a dictionary of honey accounts.

* **p.2_cookie_cruncher.py** - Extracts information about accesses from saved pages of honey accounts.

* **p.3_attributor.py** - Attributes actions in the honey accounts to accesses.

* **gas.js** - Google Apps Script. Install in honey accounts.

* **run_scraper.sh** - Runs scraper.py in headless mode.

* **run_parser.sh**  - This script contains the sequence of commands to run the parser scripts. During the first run, you may be prompted to install dependencies (please install them, they are required for the remaining scripts to work).


Subdirectories
==============

They contain code required by scripts in the **general** directory.

* **parsepop** - For email data processing.

* **loadmeta** - For loading the metadata.conf file.

* **honeylogger** - For logging.

* **normaddr** - To normalize email addresses.

* **timestamp_is_in_experiment** - To check timestamp bounds.

* **unicodeheaven** - To handle unicode data.

NOTE: This repository is a clone of https://bitbucket.org/gianluca_students/gmail-honeypot .
