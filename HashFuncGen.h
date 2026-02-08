#ifndef A3_HASHFUNCGEN_H
#define A3_HASHFUNCGEN_H

#include <cstdint>
#include <string>

class HashFuncGen {
public:
  HashFuncGen(std::uint32_t seed);

  std::uint32_t operator()(const std::string &s) const;

private:
  std::uint32_t seed_;
};

#endif