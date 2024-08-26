using System;
using System.Collections;
using System.Collections.Generic;
using Unity.VisualScripting.FullSerializer;
using UnityEngine;

public class TileWorld : MonoBehaviour
{
    [Header("Art")]
    [SerializeField] private Material tileMaterial;

    [SerializeField] private int nTiles = 5;
    [SerializeField] private int mTiles = 5;
    [SerializeField] private float tileSize = 1;
    [SerializeField] private float gap = 0.05f;
    [SerializeField] private float yOffset = 0.1f;
    [SerializeField] private Vector3 center = Vector3.zero;

    [Header("Base and Walls")]
    [SerializeField] private Material baseMaterial;
    [SerializeField] private Material wallMaterial;
    [SerializeField] private float wallHeight = 1f;
    [SerializeField] private float baseThickness = 0.1f;

    private GameObject[,] tiles;
    private Vector3 bounds;

    // Update is called once per frame
    private void Awake()
    {   
        GenerateBase();
        GenerateTiles(tileSize, nTiles, mTiles);
        GenerateWalls();
    }

    private void GenerateTiles(float tileSize, int nTiles, int mTiles)
    {   
        //Center
        yOffset += transform.position.y;
        bounds = new Vector3(nTiles/2 * tileSize, 0, nTiles / 2 * tileSize) + center;

        tiles = new GameObject[nTiles, mTiles];
        for (int n = 0; n < nTiles; n++)
        {
            for (int m = 0; m < mTiles; m++)
            {
                tiles[n, m] = GenerateTile(tileSize, n, m, gap);
            }
        }
    }

    private GameObject GenerateTile(float tileSize, int n, int m, float gap)
    {
        GameObject tileObject = new(string.Format("X:{0} Y:{1}", n, m));
        tileObject.transform.parent = transform;
        Mesh mesh = new();
        tileObject.AddComponent<MeshFilter>().mesh = mesh;
        tileObject.AddComponent<MeshRenderer>().material = tileMaterial;

        float effectiveTileSize = tileSize - gap;
        float offset = gap / 2;

        Vector3[] vertices = new Vector3[4];
        vertices[0] = new Vector3(n * tileSize + offset, yOffset, m * tileSize + offset) - bounds;
        vertices[1] = new Vector3(n * tileSize + offset, yOffset, m * tileSize + effectiveTileSize + offset) - bounds;
        vertices[2] = new Vector3(n * tileSize + effectiveTileSize + offset, yOffset, m * tileSize + offset) - bounds;
        vertices[3] = new Vector3(n * tileSize + effectiveTileSize + offset, yOffset, m * tileSize + effectiveTileSize + offset) - bounds;

        int[] tris = new int[] { 0, 1, 2, 1, 3, 2 };
        mesh.vertices = vertices;
        mesh.triangles = tris;
        mesh.RecalculateNormals();

        // Adjust the box collider to match the new tile size
        BoxCollider collider = tileObject.AddComponent<BoxCollider>();
        collider.size = new Vector3(effectiveTileSize, 0.1f, effectiveTileSize); // Adjust the Y value as needed
        collider.center = new Vector3(effectiveTileSize / 2 + offset, 0, effectiveTileSize / 2 + offset);

        return tileObject;
    }

    private void GenerateBase()
    {
        GameObject baseObject = new GameObject("Base");
        baseObject.transform.parent = transform;

        MeshFilter meshFilter = baseObject.AddComponent<MeshFilter>();
        MeshRenderer meshRenderer = baseObject.AddComponent<MeshRenderer>();

        Mesh mesh = new Mesh();
        meshFilter.mesh = mesh;
        meshRenderer.material = baseMaterial;

        float totalWidth = nTiles * tileSize;
        float totalLength = mTiles * tileSize;

        Vector3[] vertices = new Vector3[8];
        vertices[0] = new Vector3(-gap, -baseThickness, -gap);
        vertices[1] = new Vector3(totalWidth + gap, -baseThickness, -gap);
        vertices[2] = new Vector3(-gap, 0, -gap);
        vertices[3] = new Vector3(totalWidth + gap, 0, -gap);
        vertices[4] = new Vector3(-gap, -baseThickness, totalLength + gap);
        vertices[5] = new Vector3(totalWidth + gap, -baseThickness, totalLength + gap);
        vertices[6] = new Vector3(-gap, 0, totalLength + gap);
        vertices[7] = new Vector3(totalWidth + gap, 0, totalLength + gap);

        int[] triangles = new int[]
        {
        0, 2, 1, 2, 3, 1,
        1, 3, 5, 3, 7, 5,
        5, 7, 4, 7, 6, 4,
        4, 6, 0, 6, 2, 0,
        2, 6, 3, 6, 7, 3,
        0, 1, 4, 1, 5, 4
        };

        mesh.vertices = vertices;
        mesh.triangles = triangles;
        mesh.RecalculateNormals();

        baseObject.transform.position = new Vector3(-totalWidth / 2, 0, -totalLength / 2) + center;
    }

    private void GenerateWalls()
    {
        float totalWidth = nTiles * tileSize;
        float totalLength = mTiles * tileSize;

        GenerateWall(new Vector3(-totalWidth / 2 - gap, 0, 0), new Vector3(gap, wallHeight, totalLength + 2 * gap));
        GenerateWall(new Vector3(totalWidth / 2, 0, 0), new Vector3(gap, wallHeight, totalLength + 2 * gap));
        GenerateWall(new Vector3(0, 0, -totalLength / 2 - gap), new Vector3(totalWidth + 2 * gap, wallHeight, gap));
        GenerateWall(new Vector3(0, 0, totalLength / 2), new Vector3(totalWidth + 2 * gap, wallHeight, gap));
    }

    private void GenerateWall(Vector3 position, Vector3 size)
    {
        GameObject wall = GameObject.CreatePrimitive(PrimitiveType.Cube);
        wall.transform.parent = transform;
        wall.transform.localPosition = position + center;
        wall.transform.localScale = size;
        wall.GetComponent<Renderer>().material = wallMaterial;
    }
}
