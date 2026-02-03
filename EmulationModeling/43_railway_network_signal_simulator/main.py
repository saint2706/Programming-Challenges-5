from typing import Dict, List

import simpy
from simulation_core.discrete_event import DiscreteEventSimulation

from .models import RailwayConfig


class Block:
    def __init__(self, env, block_id, length):
        self.env = env
        self.id = block_id
        self.length = length
        self.resource = simpy.Resource(env, capacity=1)  # Only one train per block
        self.occupied_by = None


class Train:
    def __init__(self, train_id, speed):
        self.id = train_id
        self.speed = speed
        self.current_block = None
        self.distance_in_block = 0


class RailwaySimulation(DiscreteEventSimulation):
    def __init__(self, config: RailwayConfig):
        super().__init__(config.seed)
        self.config = config
        self.blocks: Dict[str, Block] = {}
        self.trains: List[Train] = []

        self.setup_track()
        self.setup_trains()

    def setup_track(self):
        # Simple linear track: B0 -> B1 -> ... -> Bn -> B0 (Loop)
        for i in range(self.config.num_blocks):
            bid = f"B{i}"
            self.blocks[bid] = Block(self.env, bid, self.config.block_length)

    def setup_trains(self):
        # Place trains spaced out
        spacing = self.config.num_blocks // self.config.num_trains
        for i in range(self.config.num_trains):
            t = Train(f"T{i}", self.config.train_speed)
            start_block_idx = i * spacing
            start_block_id = f"B{start_block_idx}"
            t.current_block = start_block_id
            self.trains.append(t)

            self.schedule_process(self.train_process, t)

    def train_process(self, train: Train):
        # Properly implemented rolling block reservation
        curr_idx = int(train.current_block[1:])
        curr_block = self.blocks[f"B{curr_idx}"]

        req = curr_block.resource.request()
        yield req
        curr_block.occupied_by = train.id

        while True:
            # Travel
            travel_time = curr_block.length / train.speed
            start_time = self.env.now
            while self.env.now - start_time < travel_time:
                yield self.env.timeout(1.0)
                train.distance_in_block = (self.env.now - start_time) * train.speed

            # Request next
            next_idx = (int(curr_block.id[1:]) + 1) % self.config.num_blocks
            next_block = self.blocks[f"B{next_idx}"]

            next_req = next_block.resource.request()
            yield next_req  # Wait for signal

            # Enter next
            curr_block.resource.release(req)
            curr_block.occupied_by = None

            req = next_req
            curr_block = next_block
            curr_block.occupied_by = train.id
            train.current_block = curr_block.id
            train.distance_in_block = 0

def run_simulation():
    config = RailwayConfig(duration=200)
    sim = RailwaySimulation(config)
    sim.run(until=config.duration)


if __name__ == "__main__":
    run_simulation()
