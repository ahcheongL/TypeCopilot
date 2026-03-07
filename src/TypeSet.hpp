#pragma once

#include <llvm/Support/raw_ostream.h>

#include <set>
#include <string>
#include <vector>

using namespace std;
using namespace llvm;

class TypeSet {
 private:
  set<string> types;

 public:
  bool isFunc = false;

  ~TypeSet() {
    types.clear();
  }

  void dump() {
    // iterate types and print them with a comma
    auto it = types.begin();
    for (; it != types.end(); it++) {
      errs() << *it;
      if (it != types.end()) errs() << ", ";
    }
  }

  void insert(string type) {
    types.insert(type);
    erasePtr();
  }

  void erase(string type) {
    types.erase(type);
  }

  void insert(TypeSet *other) {
    if (!other) return;

    for (auto it = other->types.begin(); it != other->types.end(); it++)
      types.insert(*it);
    erasePtr();
  }

  bool empty() {
    return types.empty();
  }

  int count(string type) {
    return types.count(type);
  }

  bool hasPtr() {
    return types.count("ptr");
  }

  bool isOpaque() {
    return types.size() == 1 && hasPtr();
  }

  bool isGenericPtr() {
    return types.size() == 1 && count("void*");
  }

  void erasePtr() {
    if (types.size() > 1 && types.count("ptr")) types.erase("ptr");
  }

  vector<string> getTypes() {
    vector<string> result;
    for (auto it = types.begin(); it != types.end(); it++)
      result.push_back(*it);
    return result;
  }

  bool equals(TypeSet *given) {
    for (auto it = given->begin(); it != given->end(); it++) {
      if (count(*it)) return true;
    }

    return false;
  }

  bool equalsBase(TypeSet *given) {
    // ground truth
    for (auto it = given->begin(); it != given->end(); it++) {
      for (auto it2 = types.begin(); it2 != types.end(); it2++) {
        string type = *it2;
        while (type.back() == '*')
          type.pop_back();
        if (type == *it) return true;
      }
    }
    return false;
  }

  int size() {
    return types.size();
  }

  string at(int index) {
    return *next(types.begin(), index);
  }

  typename set<string>::iterator begin() {
    return types.begin();
  }
  typename set<string>::iterator end() {
    return types.end();
  }
};