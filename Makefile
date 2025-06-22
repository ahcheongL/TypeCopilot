# dir
LLVM_DIR := ~/llvm-project-16/build
BUILD_DIR := build
BC := ../nginx/objs/nginx.bc 

# program option
BASELINE := false		# get the baseline
DUMP_TYPE := false  	# dump the resulting types
TYPE_SRC := 			# type source {mig, di, tbaa}
VERBOSE := false		# verbose mode
COVERAGE := false		# calculate coverage
WL := true 				# enable worklist

.PHONY: build run dump clean

build:
	cmake -B $(BUILD_DIR) -DLT_LLVM_INSTALL_DIR=$(LLVM_DIR) -DCMAKE_BUILD_TYPE=Debug
	cmake --build $(BUILD_DIR) -j $(shell nproc)

run:
	$(LLVM_DIR)/bin/opt -load-pass-plugin $(BUILD_DIR)/libTypeCopilot.so \
		-passes=typecopilot \
		-dump-type=$(DUMP_TYPE) \
		-coverage=$(COVERAGE) \
		-type-src=$(TYPE_SRC) \
		-verbose=$(VERBOSE) \
		-baseline=$(BASELINE) \
		-wl=$(WL) \
		$(BC)

tbaa:
	$(LLVM_DIR)/bin/opt -load-pass-plugin $(BUILD_DIR)/libTypeCopilot.so \
		-passes=typecopilot \
		-tbaa-acc=true \
		-baseline=$(BASELINE) \
		-type-src=$(TYPE_SRC) \
		-wl=$(WL) \
		$(BC)

dump:
	$(LLVM_DIR)/bin/opt -load-pass-plugin $(BUILD_DIR)/libTypeCopilot.so \
	    -verbose=$(VERBOSE) -type-src=$(TYPE_SRC) \
		-passes=valuedumper -f $(BC)

clean:
	-@rm -r $(BUILD_DIR)
