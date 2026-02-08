#include "HyperLogLog.h"

#include <cmath>
#include <limits>

HyperLogLog::HyperLogLog(int p) : p_(p), m_(0) {
  if (p_ < 4) {
    p_ = 4;
  }
  if (p_ > 16) {
    p_ = 16;
  }

  m_ = 1 << p_;
  reg_.assign(m_, 0);
}

int HyperLogLog::registersCount() const {
  return m_;
}

int HyperLogLog::leadingZeros32(std::uint32_t x) {
  if (x == 0u) {
    return 32;
  }

#if defined(__GNUG__)
  return __builtin_clz(x);
#else
  int cnt = 0;
  for (int i = 31; i >= 0; i -= 1) {
    if ((x & (1u << i)) != 0u) {
      break;
    }
    cnt += 1;
  }
  return cnt;
#endif
}

double HyperLogLog::alpha(int m) {
  if (m == 16) {
    return 0.673;
  }
  if (m == 32) {
    return 0.697;
  }
  if (m == 64) {
    return 0.709;
  }
  double md = m;
  return 0.7213 / (1.0 + 1.079 / md);
}

void HyperLogLog::add(std::uint32_t h) {
  std::uint32_t idx = h >> (32 - p_);
  std::uint32_t w = h << p_;

  int lz = leadingZeros32(w);
  int rho = lz + 1;

  int maxRho = (32 - p_) + 1;
  if (rho > maxRho) {
    rho = maxRho;
  }

  std::uint8_t r = rho;
  if (r > reg_[idx]) {
    reg_[idx] = r;
  }
}

double HyperLogLog::estimate() const {
  double sum = 0.0;
  int zeros = 0;

  for (int i = 0; i < m_; i += 1) {
    int v = reg_[i];
    sum += std::ldexp(1.0, -v);
    if (v == 0) {
      zeros += 1;
    }
  }

  double md = m_;
  double e = alpha(m_) * md * md / sum;

  if (e <= 2.5 * md && zeros > 0) {
    double zd = zeros;
    e = md * std::log(md / zd);
  }

  double two32 = 4294967296.0;
  if (e > (two32 / 30.0)) {
    double x = 1.0 - (e / two32);
    if (x > 0.0) {
      e = -two32 * std::log(x);
    }
  }

  return e;
}
