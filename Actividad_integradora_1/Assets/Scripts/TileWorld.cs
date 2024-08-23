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


    private GameObject[,] tiles;
    private Vector3 bounds;

    // Start is called before the first frame update
    void Start()
    {

    }

    // Update is called once per frame
    private void Awake()
    {
        GenerateTiles(tileSize, nTiles, mTiles);
    }

    private void GenerateTiles(float tileSize, int nTiles, int mTiles)
    {
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
}
