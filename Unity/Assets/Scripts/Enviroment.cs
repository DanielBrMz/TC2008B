using UnityEngine;
using System.Collections.Generic;
using UnityEditor.SearchService;
using System.Linq;
using Unity.VisualScripting;

public class Enviroment : MonoBehaviour
{
    [Header("Simulation Parameters")]
    public int agents = 4;
    public int items = 5;
    public int obstacles = 0;

    [Header("Object Parameters")]
    public GameObject AgentPrefab;


    [Header("Eviroment Parameters")]
    public static float tileSize = 3;
    public static float yOffset = 0.1f;

    [SerializeField] private int n = 10;
    [SerializeField] private int m = 10;
    // The gap affects the tile size which then translates to more space between sensors, higher gap means smaller tiles, keep the value low
    [SerializeField] private float gap = 0.05f;
    [SerializeField] private Vector3 center = Vector3.zero;

    [Header("Base and Walls")]
    [SerializeField] private float wallHeight = 4f;
    [SerializeField] private float wallGirth = 0.4f;
    [SerializeField] private float baseThickness = 0.3f;

    [Header("Materials")]
    [SerializeField] private Material tileMaterial;
    [SerializeField] private Material groundMaterial;
    [SerializeField] private Material wallMaterial;


    private GameObject[,] tiles;
    public static Vector3 bounds;
    // We add all tile renderers to this list so they can be updated later
    private List<MeshRenderer> tileRenderers = new List<MeshRenderer>();
    private static bool tilesVisible = false;
    private EnviromentManager envManager;

    private static int nTiles;
    private static int mTiles;

    // Update is called once per frame
    private void Awake()
    {
        InitializeStaticVariables();
        GenerateTiles(tileSize, nTiles, mTiles);
        GenerateWarehouse();
        InitializeObjects();
        InitializeEnvManager();
    }

    private void Update()
    {
        UpdateTileVisibility();
    }


    // Utils
    public static Vector3 CalculateObjectPosition(Vector2Int pos)
    {
        Vector3 tilePosition = new Vector3(pos.x * tileSize, yOffset, pos.y * tileSize) - bounds;
        Vector3 centeredPosition = tilePosition + new Vector3(tileSize / 2, 0, tileSize / 2);

        return centeredPosition;
    }


    private Vector2Int[] GenerateUniqueRandomPositions(int nPos)
    {
        Vector2Int[] randomPositions = new Vector2Int[nPos];
        HashSet<Vector2Int> usedPositions = new HashSet<Vector2Int>(nPos);
        int i = 0;
        while (i < nPos)
        {
            // Generate a new random position
            int k = Random.Range(0, nTiles);
            int l = Random.Range(0, mTiles);
            Vector2Int newPosition = new Vector2Int(k, l);

            // Check if the position is already used
            if (!usedPositions.Contains(newPosition))
            {
                // Add the new position to the array and the set of used positions
                randomPositions[i] = newPosition;  // Changed this line
                usedPositions.Add(newPosition);
                i++;
            }
        }
        return randomPositions;
    }

    // Updaters
    private void UpdateTileVisibility()
    {
        foreach (MeshRenderer renderer in tileRenderers)
        {
            if (renderer != null)
            {
                renderer.enabled = tilesVisible;
            }
        }
    }

    public static void ToggleTileVisibility()
    {
        tilesVisible = !tilesVisible;
    }

    // Setup
    private void InitializeEnvManager()
    {
        envManager = FindObjectOfType<EnviromentManager>();
        if (envManager == null)
        {
            GameObject managerObject = new GameObject("EnviromentManager");
            envManager = managerObject.AddComponent<EnviromentManager>();
        }

        envManager.Initialize(agents);
    }

    private void InitializeStaticVariables()
    {
        nTiles = n;
        mTiles = m;
    }

    private void InitializeObjects()
    {
        GameObject agentsWrapper = new("Agents");
        Vector2Int[] randomPositions = GenerateUniqueRandomPositions(agents + items);
        Utils.SetLayerRecursivelyByName(agentsWrapper, "Obstacles");

        int currentAgentId = 0;
        // int currentObjectId = 0;

        foreach (Vector2Int vectorPos in randomPositions)
        {
            if (currentAgentId < agents)
            {
                SpawnAgent(vectorPos, currentAgentId).transform.parent = agentsWrapper.transform;
                currentAgentId++;
            }
            // else if (currentObjectId < items)
            // {
            //     SpawnObject(i, j);
            //     objectCount -= 1;
            // }
        }
    }

    private GameObject SpawnAgent(Vector2Int pos, int id)
    {
        Vector3 position = CalculateObjectPosition(pos);
        GameObject agentObject = Instantiate(AgentPrefab, position, Quaternion.identity);

        if (agentObject.TryGetComponent<Agent>(out var agent))
        {
            agent.pos = pos;
            agent.id = id;
            agent.name = "Agent: " + id;
        }

        return agentObject;
    }

    private void GenerateTiles(float tileSize, int nTiles, int mTiles)
    {
        //Wrapper
        GameObject tilesWrapper = new GameObject("Tiles");
        tilesWrapper.transform.parent = transform;


        //Center
        yOffset += transform.position.y;
        bounds = new Vector3(nTiles * tileSize / 2, 0, mTiles * tileSize / 2) + center;

        tiles = new GameObject[nTiles, mTiles];
        for (int n = 0; n < nTiles; n++)
        {
            for (int m = 0; m < mTiles; m++)
            {
                tiles[n, m] = GenerateTile(tileSize, n, m, gap);
                tiles[n, m].transform.parent = tilesWrapper.transform;
            }
        }
    }

    private GameObject GenerateTile(float tileSize, int n, int m, float gap)
    {
        GameObject tileObject = new(string.Format("X:{0} Y:{1}", n, m));
        tileObject.transform.parent = transform;
        Mesh mesh = new();
        tileObject.AddComponent<MeshFilter>().mesh = mesh;
        MeshRenderer tileRenderer = tileObject.AddComponent<MeshRenderer>();
        tileRenderer.material = tileMaterial;

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

        // Add tile renderer to array
        tileRenderers.Add(tileRenderer);
        tileObject.layer = LayerMask.NameToLayer("Tiles");

        return tileObject;
    }

    private void GenerateWarehouse()
    {
        GameObject warehouseWrapper = new GameObject("Warehouse");
        warehouseWrapper.transform.parent = transform;

        // GenerateFloor().transform.parent = warehouseWrapper.transform;
        GenerateWalls().transform.parent = warehouseWrapper.transform;

        Utils.SetLayerRecursivelyByName(warehouseWrapper, "Obstacles");
    }


    private GameObject GenerateFloor()
    {
        GameObject floorObject = new GameObject("Floor");
        floorObject.transform.parent = transform;

        MeshFilter meshFilter = floorObject.AddComponent<MeshFilter>();
        MeshRenderer meshRenderer = floorObject.AddComponent<MeshRenderer>();

        Mesh mesh = new Mesh();
        meshFilter.mesh = mesh;
        meshRenderer.material = groundMaterial;

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

        floorObject.transform.position = new Vector3(-totalWidth / 2, 0, -totalLength / 2) + center;
        return floorObject;
    }
    private GameObject GenerateWalls()
    {
        GameObject wallsWrapper = new GameObject("Walls");

        float totalWidth = nTiles * tileSize;
        float totalLength = mTiles * tileSize;

        // Left wall
        GenerateWall(new Vector3(-totalWidth / 2 - wallGirth / 2, wallHeight / 2, 0),
                     new Vector3(wallGirth, wallHeight, totalLength + 2 * wallGirth)).transform.parent = wallsWrapper.transform;

        // Right wall
        GenerateWall(new Vector3(totalWidth / 2 + wallGirth / 2, wallHeight / 2, 0),
                     new Vector3(wallGirth, wallHeight, totalLength + 2 * wallGirth)).transform.parent = wallsWrapper.transform;

        // Back wall
        GenerateWall(new Vector3(0, wallHeight / 2, -totalLength / 2 - wallGirth / 2),
                     new Vector3(totalWidth + 2 * wallGirth, wallHeight, wallGirth)).transform.parent = wallsWrapper.transform;

        // Front wall
        GenerateWall(new Vector3(0, wallHeight / 2, totalLength / 2 + wallGirth / 2),
                     new Vector3(totalWidth + 2 * wallGirth, wallHeight, wallGirth)).transform.parent = wallsWrapper.transform;

        return wallsWrapper;
    }

    private GameObject GenerateWall(Vector3 position, Vector3 size)
    {
        GameObject wall = GameObject.CreatePrimitive(PrimitiveType.Cube);
        wall.transform.parent = transform;
        wall.transform.localPosition = position + center;
        wall.transform.localScale = size;
        wall.GetComponent<Renderer>().material = wallMaterial;

        wall.layer = LayerMask.NameToLayer("Obstacles");

        // Ensure the wall has a BoxCollider
        BoxCollider collider = wall.GetComponent<BoxCollider>();
        if (collider == null)
        {
            collider = wall.AddComponent<BoxCollider>();
        }

        return wall;
    }
}
