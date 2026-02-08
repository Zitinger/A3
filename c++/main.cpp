#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <unordered_set>
#include <cstdint>

#include "RandomStreamGen.h"
#include "HashFuncGen.h"
#include "HyperLogLog.h"

static void runOneStream(
  int streamId,
  const std::vector<std::string> &stream,
  const std::vector<int64_t> &checkpoints,
  const HashFuncGen &hashFunc,
  int p,
  std::ofstream &out
) {
  HyperLogLog hll(p);
  std::unordered_set<std::string> exact;
  exact.reserve(stream.size() * 2);

  int64_t nextIdx = 0;
  int step = 0;

  for (int64_t i = 0; i < stream.size(); i += 1) {
    const std::string &s = stream[i];

    exact.insert(s);
    std::uint32_t h = hashFunc(s);
    hll.add(h);

    while (nextIdx < checkpoints.size() && (i + 1) == checkpoints[nextIdx]) {
      int64_t processed = checkpoints[nextIdx];
      int64_t trueF0 = exact.size();
      double est = hll.estimate();

      double frac = 0.0;
      if (!stream.empty()) {
        frac = double(processed) / stream.size();
      }

      out << streamId << ",";
      out << step << ",";
      out << frac << ",";
      out << processed << ",";
      out << trueF0 << ",";
      out << est << "\n";

      nextIdx += 1;
      step += 1;
    }
  }
}

int main(int argc, char **argv) {
  int streamsCount = 20;
  int64_t streamSize = 200000;
  int stepPercent = 5;
  int p = 10;
  std::uint64_t seed = 12345;

  if (argc >= 2) {
    streamsCount = std::stoi(argv[1]);
  }
  if (argc >= 3) {
    streamSize = std::stoll(argv[2]);
  }
  if (argc >= 4) {
    stepPercent = std::stoi(argv[3]);
  }
  if (argc >= 5) {
    p = std::stoi(argv[4]);
  }
  if (argc >= 6) {
    seed = std::stoull(argv[5]);
  }

  HashFuncGen hashFunc(777);

  std::ofstream out("results.csv");
  out << "stream_id,step,fraction,processed,true_f0,estimate\n";

  for (int i = 0; i < streamsCount; i += 1) {
    RandomStreamGen gen(streamSize, seed + i * 1000ULL);
    std::vector<int64_t> cps = gen.checkpointsByPercent(stepPercent);

    runOneStream(i, gen.data(), cps, hashFunc, p, out);
  }

  out.close();

  std::cout << "OK: results.csv generated\n";
  return 0;
}
