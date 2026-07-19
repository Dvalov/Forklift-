import heapq


def astar(start: tuple, goal: tuple, obstacles: set) -> list | None:
    """
    A* pathfinding on a 2D (x, z) Manhattan grid.

    Args:
        start:     (x, z) tuple — forklift current position (floats coerced to int)
        goal:      (x, z) tuple — task destination cell (already int)
        obstacles: set of (x, z) tuples that are blocked (Cell records from Warehouse API)

    Returns:
        []         if start == goal (forklift already at destination)
        None       if no path exists (destination unreachable)
        list       of {"x": int, "z": int} dicts, start exclusive, goal inclusive
    """
    start = (int(start[0]), int(start[1]))
    goal = (int(goal[0]), int(goal[1]))

    if start == goal:
        return []

    # CRITICAL: goal cell is always present in the obstacle set because all Cell records
    # are obstacles (decision A-2). Discard the goal so the forklift can reach its target.
    obstacles = set(obstacles)  # copy — do not mutate caller's set
    obstacles.discard(goal)

    if start in obstacles:
        # Start position blocked — cannot move at all
        return None

    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # heap entries: (f_score, g_score, node, path_so_far)
    open_heap = []
    heapq.heappush(open_heap, (heuristic(start, goal), 0, start, []))
    visited = set()

    while open_heap:
        f, g, current, path = heapq.heappop(open_heap)

        if current in visited:
            continue
        visited.add(current)

        if current == goal:
            full_path = path + [current]
            return [{"x": x, "z": z} for x, z in full_path if (x, z) != start]

        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = current[0] + dx, current[1] + dz
            neighbor = (nx, nz)
            if neighbor in visited:
                continue
            if neighbor in obstacles:
                continue
            new_g = g + 1
            new_f = new_g + heuristic(neighbor, goal)
            heapq.heappush(open_heap, (new_f, new_g, neighbor, path + [current]))

    return None  # No path found
