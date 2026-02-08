#ifndef A3_RANDOMSTREAMGEN_H
#define A3_RANDOMSTREAMGEN_H

#include <cstdint>
#include <string>
#include <vector>
#include <random>

class RandomStreamGen {
public:
  RandomStreamGen(int64_t streamSize, std::uint64_t seed);

  const std::vector<std::string> &data() const;

  std::vector<int64_t> checkpointsByPercent(int stepPercent) const;

private:
  std::vector<std::string> data_;
  std::mt19937_64 rng_;

  char nextChar();

  int nextLen();
};


#endif
