using System.Collections;
using System.Runtime.InteropServices;
using Unity.VisualScripting;
using UnityEditor;
using UnityEngine;
using UnityEngine.AI;

public class Agent : MonoBehaviour
{
    [Header("Agent values")]
    public int id;
    public Vector2Int pos;
    public int[] cols;


    [Header("Sensor configuration")]
    [SerializeField] private Vector3 sensorOffset = new Vector3(0f, 0.5f, 0f); // Offset from the agent's center
    // [SerializeField] private float sensorVerticalOffset = 0.5f;
    [SerializeField] private float sensorSize = 1f;
    [SerializeField] private Material sensorMaterial;

    //Model values
    private readonly Transform orientation; // this will probably go unused unless we implement animations or models

    // Sensor values
    private GameObject sensorsContainer; // Wrapper for the colliders
    private GameObject[] sensors;
    private int[] sensorValues; // 0: nothing, 1: another agent, 2: object
    public static bool showColliders = false;

    // Enviroment
    private Vector3 targetPosition;
    private Coroutine moveCorutine;
    private float sensorDistance;


    private void Awake()
    {
        SetupCollisionMatrix();
        GenerateSensors();
        EnviromentManager.OnAgentAction += ActionManager;
        sensorDistance = Enviroment.tileSize;
    }


    void Update()
    {
        UpdateSensorPositions();
        UpdateColliderVisibility();
    }

    // Utils
    private readonly Vector2Int[] directions = new Vector2Int[]
    {
        Vector2Int.up,
        Vector2Int.down,
        Vector2Int.left,
        Vector2Int.right
    };

    private string Direction2Name(Vector2Int direction)
    {
        if (direction == Vector2Int.up) return "F";
        if (direction == Vector2Int.down) return "B";
        if (direction == Vector2Int.left) return "L";
        if (direction == Vector2Int.right) return "R";
        return ""; // Default case, should not happen with your current directions array
    }

    public static readonly char[] directionNames = { 'F', 'B', 'L', 'R' };

    private Vector2Int Name2Direction(char name)
    {
        switch (name)
        {
            case 'F':
                return Vector2Int.up;
            case 'B':
                return Vector2Int.down;
            case 'L':
                return Vector2Int.left;
            case 'R':
                return Vector2Int.right;
            default:
                Debug.LogError($"Invalid direction name: {name}.");
                return pos;
        }
    }

    public void ActionManager(int agentId, string instruction)
    {
        if (id != agentId)
        {
            return;
        }

        if (instruction.Length != 2)
        {
            Debug.LogError($"Invalid instruction string format: {instruction}.");
            return;
        }

        char action = instruction[0];
        char direction = instruction[1];

        switch (action)
        {
            case 'M':
                Move(direction);
                break;
            default:
                Debug.Log($"Action not implemented yet: {instruction}");
                break;
        }
    }

    // Updaters
    public void Move(char direction)
    {
        // if (!IsColliding(direction))
        // {

        // }

        pos += Name2Direction(direction);
        targetPosition = Enviroment.CalculateObjectPosition(pos);

        if (moveCorutine != null)
        {
            StopCoroutine(moveCorutine);
        }

        moveCorutine = StartCoroutine(UpdatePosition());
    }

    // private bool IsColliding(char direction)
    // {

    // }

    private IEnumerator UpdatePosition()
    {
        Debug.Log($"Agent:{id} moves!");
        Vector3 startPos = transform.position;
        float elapsedTime = 0f;

        while (elapsedTime < EnviromentManager.iterationDelay)
        {
            elapsedTime += Time.deltaTime;
            float t = Mathf.Clamp01(elapsedTime / EnviromentManager.iterationDelay);
            transform.position = Vector3.Lerp(startPos, targetPosition, t);
            yield return null;

        }

        transform.position = targetPosition;
        moveCorutine = null;
    }


    // This function can be hijacked to send the data to he server
    public void UpdateSensorValue(int sensorIndex, int value)
    {
        sensorValues[sensorIndex] = value;
    }

    private void UpdateSensorPositions()
    {
        for (int i = 0; i < sensors.Length; i++)
        {
            sensors[i].transform.position = transform.position;
            // sensors[i].transform.rotation = transform.rotation;
        }
    }


    private void UpdateColliderVisibility()
    {
        foreach (GameObject sensor in sensors)
        {
            sensor.transform.GetChild(0).gameObject.SetActive(showColliders);
        }
    }

    public static void ToggleColliderVisibility()
    {
        showColliders = !showColliders;
    }

    // Sensor Setup
    // This setups to what the colliders will be able to collide with
    private void SetupCollisionMatrix()
    {
        // Sensors only interact with Agents, Objects, and Obstacles
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensors"), LayerMask.NameToLayer("Sensors"), true);
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensors"), LayerMask.NameToLayer("Obstacles"), false);
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensors"), LayerMask.NameToLayer("Stacks"), false);
    }

    private void GenerateSensors()
    {
        // Create the sensors container
        sensorsContainer = new GameObject("SensorsContainer");
        sensorsContainer.transform.SetParent(transform);
        sensorsContainer.transform.localPosition = Vector3.zero;

        sensors = new GameObject[directions.Length];
        sensorValues = new int[directions.Length];

        for (int i = 0; i < directions.Length; i++)
        {
            string directionName = Direction2Name(directions[i]);
            sensors[i] = GenerateSensor($"Sens{directionName}", directions[i]);
            sensors[i].transform.SetParent(sensorsContainer.transform);
            sensorValues[i] = 0;
        }
    }

    private GameObject GenerateSensor(string name, Vector2Int direction)
    {
        GameObject sensor = new GameObject(name);
        sensor.transform.SetParent(transform); // Set the subject of this script as the parent
        sensor.layer = LayerMask.NameToLayer("Sensors");


        SphereCollider collider = sensor.AddComponent<SphereCollider>();
        collider.isTrigger = true;
        collider.radius = sensorSize / 2;
        collider.center = FlatDir23DDir(direction) * sensorDistance + sensorOffset;

        SensorTrigger trigger = sensor.AddComponent<SensorTrigger>();
        trigger.parentAgent = this;
        trigger.sensorIndex = System.Array.IndexOf(directions, direction);

        // Crate visualizer
        GameObject visualizer = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        visualizer.transform.SetParent(sensor.transform);
        visualizer.transform.localPosition = collider.center;
        visualizer.transform.localScale = Vector3.one * (sensorSize / 2 * 2);
        Destroy(visualizer.GetComponent<SphereCollider>()); // Remove colliders since they are not needed
        visualizer.transform.GetComponent<Renderer>().material = sensorMaterial;
        visualizer.SetActive(showColliders);

        return sensor;
    }

    private Vector3 FlatDir23DDir(Vector2Int direction)
    {
        if (direction == Vector2Int.up) return Vector3.forward;
        if (direction == Vector2Int.down) return Vector3.back;
        if (direction == Vector2Int.left) return Vector3.left;
        if (direction == Vector2Int.right) return Vector3.right;
        return Vector3.zero; // Default case, should not happen with your current directions array
    }

}
