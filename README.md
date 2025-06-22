# TypeCopilot

TypeCopilot is the type inference prototype of ISSTA'25 *Type-Alias Analysis: Enabling LLVM IR with Accurate Types*. [[paper](https://doi.org/10.1145/3728974)] [[artifact](https://zenodo.org/records/15182810)]


## Getting Started

This section walks through setting up the environment and running TypeCopilot on a sample bitcode file (OpenSSL.bc).

### Get & Build LLVM Dependencies

We provide a script `script/llvm.py` to compile LLVM dependencies.
In the script, the last number is the parallelism number. Please adjust the parallel number based on your machine.

```sh
python3 script/llvm.py build 16 <parallel_number>
```

### Run TypeCopilot on OpenSSL Bitcode

```sh
make
make run BC=bc/openssl.bc DUMP_TYPE=true TYPE_SRC=comb &>/dev/null 2>openssl.comb.txt
```

This will:
- Build TypeCopilot
- Run it against the OpenSSL bitcode file
- Save the output to `openssl.comb.txt`

### Verify Output

To check the results, run:

```sh
cat openssl.comb.txt
```

Expected format:

```
<function>, <IR value name>, { <type alias set> }
```

**Understanding the Output**:
Each line in the output follows this format:

1. The function name where the type alias was discovered
2. The LLVM IR value name
3. The corresponding type alias set (shown within curly braces)

Example output:

```
...
ssl_srp_server_param_cb, ret.0, { i32 }
ssl_srp_server_param_cb, retval.0, { i32 }
lookup_srp_user, srp_callback_parm, { %struct.srpsrvparm_st* }
lookup_srp_user, bio_s_out, { %struct.bio_st* }
lookup_srp_user, user, { %struct.SRP_user_pwd_st**, i8** }
...
```


### More Details

If you find the paper helpful, please consider citing it:

```
@inproceedings{type-alias-analysis,
  title     = {Type-Alias Analysis: Enabling LLVM IR with Accurate Types},
  author    = {Jinmeng Zhou and Ziyue Pan and Wenbo Shen and Xingkai Wang and Kangjie Lu and Zhiyun Qian},
  booktitle = {Proceedings of the 34th ACM SIGSOFT International Symposium on Software Testing and Analysis},
  year      = {2025},
  location  = {Trondheim, Norway},
  doi       = {10.1145/3728974},
}
```