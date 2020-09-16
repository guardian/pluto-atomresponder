package main

import (
	"flag"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/kinesis"
	"io/ioutil"
	"log"
	"os"
)

func get_file(filename string) *[]byte {
	log.Printf("Reading from %s...", filename)
	fp, openErr := os.Open(filename)
	if openErr != nil {
		log.Fatalf("Could not open %s: %s", filename, openErr)
	}
	defer fp.Close()

	content, readErr := ioutil.ReadAll(fp)
	if readErr != nil {
		log.Fatalf("Could not read from %s: %s", filename, readErr)
	}

	return &content
}

func main() {
	filenamePtr := flag.String("file", "", "File whose contents will be sent")
	streamNamePtr := flag.String("stream", "", "Stream to send the data to")
	flag.Parse()

	//get credentails from default chain - https://docs.aws.amazon.com/sdk-for-go/api/
	sess, sessionErr := session.NewSession()
	if sessionErr != nil {
		log.Fatal("Could not set up AWS session: ", sessionErr)
	}

	svc := kinesis.New(sess)

	contentPtr := get_file(*filenamePtr)
	partKey := "1"
	rq := &kinesis.PutRecordInput{
		Data:         *contentPtr,
		PartitionKey: &partKey,
		StreamName:   streamNamePtr,
	}

	log.Printf("Sending to %s", *streamNamePtr)
	_, sendErr := svc.PutRecord(rq)
	if sendErr != nil {
		log.Fatal("Could not send to stream: ", sendErr)
	}
	log.Print("Successfully sent")
}
