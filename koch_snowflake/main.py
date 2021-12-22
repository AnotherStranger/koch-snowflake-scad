import click
import openpyscad as ops
import numpy as np
from typing import List
import plotly.express as px
import pandas as pd


@click.command()
@click.option("--size", type=float, default=100, help="Side length of the initial triangle in mm.")
@click.option(
    "--iterations",
    type=click.IntRange(0, 20),
    default=5,
    help="Number of fractal iterations. More iterations yield more complex snowflakes",
)
@click.option("--thickness", type=float, default=1, help="Thickness of the snowflake in mm.")
@click.option("--with-hole/--without-hole", default=True, help="Whether you want a hole for hanging the snowflake.")
@click.option("--hole-radius", type=float, default=1, help="The radius of the hole in mm.")
@click.option(
    "--hole-clearance", type=float, default=1.2, help="The clearance of the hole to the outer perimeter in mm."
)
@click.argument("out_file", type=click.Path(dir_okay=False), required=True)
def main(
    size: float,
    iterations: int,
    thickness: float,
    with_hole: bool,
    hole_radius: float,
    hole_clearance: float,
    out_file: str,
):
    all_points = koch_snowflake(size, iterations)

    snowflake = ops.Polygon(all_points).linear_extrude(thickness)
    scad_object = snowflake

    if with_hole:
        triangle_height = (3.0 / 4 * size ** 2) ** 0.5  # This is the height of the initial triangle

        # calculate distance from top using the intercept theorem
        distance_from_top = triangle_height * ((hole_radius + hole_clearance) / (1.0 / 2.0 * size))

        # Create a cylinder as hole and substract from the snowflake
        hole = ops.Cylinder(r=hole_radius, h=thickness * 3, _fn=100).translate(
            [size / 2, triangle_height - distance_from_top, -thickness]
        )
        difference = ops.Difference()
        difference.append(snowflake)
        difference.append(hole)
        scad_object = difference

    scad_object.write(out_file)


def koch_snowflake(size: float, iterations) -> List[List[float]]:
    """
    Creates a koch snowflake of given size

    :param size: size of the snowflakes base triangle in mm.
    :param iterations: number of fractal iterations

    :returns: a list of all snowflake points
    """
    triangle_height = (3.0 / 4 * size ** 2) ** 0.5
    points1 = koch_curve(np.array([0, 0]), np.array([size / 2, triangle_height]), n=iterations)
    points2 = koch_curve(np.array([size / 2, triangle_height]), np.array([size, 0]), n=iterations)
    points3 = koch_curve(np.array([size, 0]), np.array([0, 0]), n=iterations)
    all_points = [arr.tolist() for arr in points1 + points2 + points3]
    return all_points


def koch_curve(x1: np.array, x2: np.array, n: int = 1, modify: float = 1) -> List[np.array]:
    """
    Creates a koch curve with a given start and end point using recursion

    :param x1: start point of the curve
    :param x2: end point of the curve
    :param n: number of iterations (recursions)
    :param modify: change the direction of the norm vectors should be either 1 or -1. Set to -1 if curve is facing the wrong direction.

    :return: A list consisting of all points in the koch curve
    """

    # stop recursion if number of iterations is less than 1
    if n <= 0:
        return [x1, x2]
    else:
        con_vec = x2 - x1
        line_len = np.linalg.norm(con_vec)

        norm_vec = modify * np.array([-1 * con_vec[1], con_vec[0]]) / line_len

        line_mid = 0.5 * (x1 + x2)

        p1 = x1  # start point
        p2 = p1 + 1.0 / 3.0 * con_vec  # triangle base
        p3 = line_mid + norm_vec * (line_len / (12 ** 0.5))  # triangle point
        p4 = x1 + 2.0 / 3.0 * con_vec  # triangle base
        p5 = x2  # end point

        # apply recursion to each new segment
        part_1 = koch_curve(p1, p2, n - 1, modify)
        part_2 = koch_curve(p2, p3, n - 1, modify)
        part_3 = koch_curve(p3, p4, n - 1, modify)
        part_4 = koch_curve(p4, p5, n - 1, modify)

        return part_1 + part_2 + part_3 + part_4
