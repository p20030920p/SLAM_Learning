// Copyright (c) 2026 p20030920p and zfyyyyy
// SPDX-License-Identifier: MIT

#ifndef ALGO_CORE__GRAPH__ASTAR_HPP_
#define ALGO_CORE__GRAPH__ASTAR_HPP_

#include <string>

#include "algo_core/grid_planner.hpp"

namespace algo_core
{

/// A* on the 8-connected cost grid.
///
/// The priority function is f = g + h, with h the octile distance to the goal
/// (Manhattan when diagonal moves are disabled). Everything else — the cost
/// model, the corner cutting rule, the path rebuilding — is shared with the
/// rest of the library, so this class is only the search itself.
class AStarPlanner final : public GridPlanner
{
public:
  std::string name() const override {return "astar";}

  PlanResult plan(const CostGrid & grid, const Pose2D & start, const Pose2D & goal) override;
};

}  // namespace algo_core

#endif  // ALGO_CORE__GRAPH__ASTAR_HPP_
