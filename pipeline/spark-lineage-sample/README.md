# Simple sparkjob for testing Marquez lineage



## Prerequisites

The instructions below assume you have a Unix-like environment.

You will need to have the following setup in your local environment or wherever you choose to run this test:

* JDK 8+
* sbt 1.3.x+

## Running Locally


* Clone this repo
* Set the memory options, 4GB should be Ok
```
$ export SBT_OPTS="-Xmx4G"
```
* Run the UserSongSessionStats app with 
```
$ sbt "runMain org.spark.lineage.LineageApp ../data/input.parquet ../data/ouput"
```
I think it will work at once but if you encounter any issue, feel free to contact me.

## Tests


The are a few tests created for validating basic behavior. All tests can be run locally by simple invoking sbt test target:
```
$ sbt test
``` 
