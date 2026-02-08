#include "HashFuncGen.h"

HashFuncGen::HashFuncGen(std::uint32_t seed) : seed_(seed) {
}

std::uint32_t HashFuncGen::operator()(const std::string &s) const {
  std::uint32_t h = 2166136261u ^ seed_;
  for (std::size_t i = 0; i < s.size(); i += 1) {
    h ^= s[i];
    h *= 16777619u;
  }
  return h;
}
