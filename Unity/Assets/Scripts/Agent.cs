using System.Collections;
using System.Collections.Generic;
using Unity.VisualScripting;
using UnityEngine;

public class Agent : MonoBehaviour
{
    [Header("Agent values")]
    public int id;
    public Vector2Int pos;
    public Dictionary<char, int> cols = new Dictionary<char, int>
    {
    {'F', 0},
    {'B', 0},
    {'L', 0},
    {'R', 0}
    };
    public bool hasCollided = false;


    [Header("Sensor configuration")]
    [SerializeField] private Material sensorMaterial;

    //Model values
    private readonly Transform orientation; // this will probably go unused unless we implement animations or models

    // Sensor values
    private GameObject sensorsContainer; // Wrapper for the colliders
    private GameObject contactSensor;
    private SensorTrigger[] sensors;
    public static bool showColliders = false;

    // Enviroment
    private Vector3 targetPosition;
    private Coroutine moveCorutine;

    private void Awake()
    {

        SetupCollisionMatrix();
        GenerateSensors();
        EnviromentManager.OnAgentAction += ActionManager;
    }


    void Update()
    {
        UpdateSensorPositions();
        UpdateContactSensorPosition();
        UpdateColliderVisibility();
    }

    // Utils
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

    private string Col2Type(int col)
    {
        switch (col)
        {
            case 1:
                return "Object";
            case 2:
                return "Obstacle";
            case 3:
                return "Stack";
            default:
                return "Undefined";
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
                Move(direction, EnviromentManager.iterationDelay);
                break;
            default:
                Debug.Log($"Action not implemented yet: {instruction}");
                break;
        }
    }

    // Updaters
    public void Move(char direction, float timeToMove)
    {
        // Check for initial collision
        int value = IsColliding(direction);
        Vector2Int newPos = pos + Name2Direction(direction);
        if (value != 0)
        {
            Debug.LogWarning($"Ag:{id} tried to move into an {Col2Type(value)}!");
            return;
        }

        hasCollided = false;
        pos = newPos;

        // Calculate the new target position
        targetPosition = Enviroment.CalculateObjectPosition(pos);

        // Handle coroutine for updating position
        if (moveCorutine != null)
        {
            StopCoroutine(moveCorutine);
        }
        moveCorutine = StartCoroutine(UpdatePosition(direction, timeToMove));
    }

    private int IsColliding(char direction)
    {

        int value = cols[direction];

        if (value != 0)
            return value;
        else
            return 0;
    }

    private IEnumerator UpdatePosition(char direction, float timeToMove)
    {
        Vector3 startPos = transform.position;
        float elapsedTime = 0f;
        while (elapsedTime < timeToMove)
        {
            elapsedTime += Time.deltaTime;
            float t = Mathf.Clamp01(elapsedTime / timeToMove);
            transform.position = Vector3.Lerp(startPos, targetPosition, t);

            if (hasCollided)
            {   
                StopCoroutine(moveCorutine);
                Debug.LogError($"Ag:{id} collided with another agent!");
                float remainingTime = timeToMove - elapsedTime;
                Move(Utils.OppositeDir(direction), remainingTime);
                yield break;
            }

            yield return null;
        }
        transform.position = targetPosition;
        moveCorutine = null;
    }


    public void UpdateSensorValue(char direction, int value)
    {
        cols[direction] = value;
        Debug.Log($"Cols for Ag:{id}:" + string.Join(", ", cols));
    }

    private void UpdateSensorPositions()
    {
        for (int i = 0; i < sensors.Length; i++)
        {
            sensors[i].transform.position = transform.position;
            // sensors[i].transform.rotation = transform.rotation;
        }
    }

    private void UpdateContactSensorPosition()
    {
        contactSensor.transform.position = transform.position + new Vector3(0f,1.5f,0f);
    }


    private void UpdateColliderVisibility()
    {
        foreach (SensorTrigger sensor in sensors)
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
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensors"), LayerMask.NameToLayer("Tiles"), true);
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensors"), LayerMask.NameToLayer("Obstacles"), false);
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensors"), LayerMask.NameToLayer("Stacks"), false);
    }

    private void GenerateSensors()
    {
        // Create the sensors container
        sensorsContainer = new GameObject("SensorsContainer");
        sensorsContainer.transform.SetParent(transform);
        sensorsContainer.transform.localPosition = Vector3.zero;

        sensors = new SensorTrigger[Utils.directions.Length];

        sensors[0] = GenerateSensor("Sens:F", Utils.directions[0]);
        sensors[1] = GenerateSensor("Sens:B", Utils.directions[1]);
        sensors[2] = GenerateSensor("Sens:L", Utils.directions[2]);
        sensors[3] = GenerateSensor("Sens:R", Utils.directions[3]);

        foreach (SensorTrigger sensor in sensors)
        {
            sensor.transform.parent = sensorsContainer.transform;
        }

        Utils.SetLayerRecursivelyByName(sensorsContainer, "Sensors");

        GameObject contactSensorWrapper = new GameObject("ContactSensor");

        contactSensor = GenerateContactSensor("ConSensor");
        contactSensor.transform.parent = contactSensorWrapper.transform;
        contactSensor.layer = LayerMask.NameToLayer("Contact");

        Utils.SetLayerRecursivelyByName(contactSensorWrapper, "Contact");
    }

    private SensorTrigger GenerateSensor(string name, Vector2Int direction)
    {
        GameObject sensor = new GameObject(name);
        sensor.transform.SetParent(transform); // Set the subject of this script as the parent
        sensor.layer = LayerMask.NameToLayer("Sensors");


        SphereCollider collider = sensor.AddComponent<SphereCollider>();
        collider.isTrigger = true;
        collider.radius = (Enviroment.tileSize / 2);
        collider.center = FlatDir23DDir(direction) * (Enviroment.tileSize - 0.5f) + new Vector3(0, 0.5f, 0);

        SensorTrigger trigger = collider.AddComponent<SensorTrigger>();
        trigger.parentAgent = this;
        trigger.direction = Utils.Direction2Name(direction);

        // Crate visualizer
        GameObject visualizer = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        visualizer.transform.SetParent(sensor.transform);
        visualizer.transform.localPosition = collider.center;
        visualizer.transform.localScale = Vector3.one * (Enviroment.tileSize / 2 * 2);
        Destroy(visualizer.GetComponent<SphereCollider>()); // Remove colliders since they are not needed
        visualizer.transform.GetComponent<Renderer>().material = sensorMaterial;
        visualizer.SetActive(showColliders);

        return trigger;
    }

    private GameObject GenerateContactSensor(string name)
    {
        GameObject sensor = new GameObject(name);
        sensor.transform.SetParent(transform);
        sensor.layer = LayerMask.NameToLayer("Obstacles");

        BoxCollider collider = sensor.AddComponent<BoxCollider>();
        collider.isTrigger = true;
        collider.size = new Vector3(0.8f,0.8f,0.8f);
        collider.center = Vector3.zero;

        ContactTrigger trigger = collider.AddComponent<ContactTrigger>();
        trigger.parentAgent = this;
        
        return sensor;
    }

    private Vector3 FlatDir23DDir(Vector2Int direction)
    {
        if (direction == Vector2Int.up) return Vector3.forward;
        if (direction == Vector2Int.down) return Vector3.back;
        if (direction == Vector2Int.left) return Vector3.left;
        if (direction == Vector2Int.right) return Vector3.right;
        return Vector3.zero; // Default case, should not happen with your current Utils.directions array
    }

}
