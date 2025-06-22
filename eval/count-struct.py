import sys

# get struct name
def get_struct(line):
    definition = line.split(" ")[0]
    definition = definition.replace("%struct.", "")

    # remove the ending dot and numbers
    if "." in definition:
        definition = definition.split(".")[0]

    return definition

# count
def count_struct(filename):
    structset = set()  # unique struct
    count = 0  # total count
    has_dup_struct_set = set()

    struct_start = False
    with open(filename, "r") as f:
        for line in f:
            # get non-anonymous structs
            # if line.startswith("%struct") and not line.startswith("%struct.anon"):
            if line.startswith("%struct"):
                if not struct_start:
                    struct_start = True

                count += 1
                unique_struct = get_struct(line)
                if unique_struct in structset:
                    print("[DEBUG] duplicate struct: %s" % line)
                    has_dup_struct_set.add(unique_struct)
                structset.add(unique_struct)

            # end of struct section
            if struct_start and not line.startswith("%"):
                break
    return count, len(structset), len(has_dup_struct_set)


# given a file path, return the number of struct
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python count-struct.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    total, unique, has_dup_count = count_struct(filename)
    print("Number of structs: %d" % total)
    print("Number of unique structs: %d" % unique)
    print("Number of structs has duplicate: %d" % has_dup_count)
