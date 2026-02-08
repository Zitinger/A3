#include "RandomStreamGen.h"

RandomStreamGen::RandomStreamGen(int64_t streamSize, std::uint64_t seed) : rng_(seed) {
  data_.reserve(streamSize);

  for (int64_t i = 0; i < streamSize; i += 1) {
    int len = nextLen();
    std::string s;
    s.reserve(len);

    for (int j = 0; j < len; j += 1) {
      s.push_back(nextChar());
    }

    data_.push_back(s);
  }
}

const std::vector<std::string> &RandomStreamGen::data() const {
  return data_;
}

std::vector<int64_t> RandomStreamGen::checkpointsByPercent(int stepPercent) const {
  std::vector<int64_t> res;

  if (stepPercent <= 0) {
    stepPercent = 10;
  }
  if (stepPercent > 100) {
    stepPercent = 100;
  }

  int64_t n = data_.size();
  int percent = stepPercent;

  while (percent <= 100) {
    int64_t cnt = (n * percent) / 100;
    if (cnt < 0) {
      cnt = 0;
    }
    if (cnt > n) {
      cnt = n;
    }
    res.push_back(cnt);
    percent += stepPercent;
  }

  if (res.empty() || res.back() != n) {
    res.push_back(n);
  }

  return res;
}

char RandomStreamGen::nextChar() {
  static const std::string chars =
      "abcdefghijklmnopqrstuvwxyz"
      "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
      "0123456789"
      "-";

  std::uniform_int_distribution<int> dist(0, chars.size() - 1);
  return chars[dist(rng_)];
}

int RandomStreamGen::nextLen() {
  std::uniform_int_distribution<int> dist(1, 30);
  return dist(rng_);
}
