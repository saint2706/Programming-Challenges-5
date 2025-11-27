"""Particle system engine with list and NumPy vectorized update paths."""

from .particle_engine import Particle, ParticleEngine, run_sample_animation

__all__ = ["Particle", "ParticleEngine", "run_sample_animation"]
