#ifndef A3_HYPERLOGLOG_H
#define A3_HYPERLOGLOG_H

#include <cstdint>
#include <vector>
#include <string>

class HyperLogLog {
public:
  HyperLogLog(int p);

  void add(std::uint32_t h);

  double estimate() const;

  int registersCount() const;

private:
  int p_;
  int m_;
  std::vector<std::uint8_t> reg_;

  static int leadingZeros32(std::uint32_t x);
  static double alpha(int m);
};

#endif