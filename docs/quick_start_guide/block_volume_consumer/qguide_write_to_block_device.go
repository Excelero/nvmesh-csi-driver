package main

import (
    "fmt"
	"io/ioutil"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func check(e error) {
    if e != nil {
        panic(e)
    }
}

func SetupCloseHandler() {
    c := make(chan os.Signal, 2)
    signal.Notify(c, syscall.SIGINT, syscall.SIGTERM)
    go func() {
        <-c
        fmt.Println("\r- Exiting..")
        os.Exit(0)
    }()
}

func main() {

	SetupCloseHandler()

	if len(os.Args) == 1 {
		fmt.Println("Error: no file path given. The first argument should be the block device file path")
		os.Exit(1)
	}

	filename := os.Args[1]
	// Write To File
	fmt.Printf("Writing to file %s\n", filename)
	bytes_to_write := []byte("Excelero NVMesh")
	err := ioutil.WriteFile(filename, bytes_to_write, 0644)
	check(err)

	// Open file
	f, err := os.Open(filename)
	check(err)

	// Read bytes from file
	write_size := len(bytes_to_write)
	bytes_read := make([]byte, write_size)
	size, err := f.Read(bytes_read)
	check(err)

	// Print output
	fmt.Printf("Read %d bytes: \"%s\"\n", size, string(bytes_read[:size]))

	// loop until SIGTERM
    for {
        fmt.Println("- Sleeping")
        time.Sleep(10 * time.Second)
    }
}