using System.Collections;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Unity.VisualScripting;
using Unity.VisualScripting.Antlr3.Runtime.Collections;
using UnityEngine;

public class Object : MonoBehaviour
{
    [Header("Parameters")]
    public float size = 2f;

    [Header("Prefabs")]
    [SerializeField] private GameObject[] models;

    private static bool colliderVisible = false;

    public bool isGrabbed = false;
    public bool isMoving = false;
    public Transform grabber;

    private SemaphoreSlim grabLock = new SemaphoreSlim(1, 1);
    private bool isBeingGrabbed = false;


    private void Awake()
    {
        transform.localScale = Vector3.one * size;
        SetRandomModel();
    }

    private void Update()
    {
        UpdateObjectColliderVisibility();
    }

    private void UpdateObjectColliderVisibility()
    {
        transform.GetComponent<Renderer>().enabled = colliderVisible;
    }

    public static void ToggleItemColliderVisibility()
    {
        colliderVisible = !colliderVisible;
    }

    public async Task<bool> TryGrab()
    {
        await grabLock.WaitAsync();
        try
        {
            if (isBeingGrabbed)
            {
                return false;
            }
            isBeingGrabbed = true;
            return true;
        }
        finally
        {
            grabLock.Release();
        }
    }
    public void CancelGrab()
    {
        isBeingGrabbed = false;
    }

    public void ObjGrab(Transform newGrabber)
    {
        isGrabbed = true;
        grabber = newGrabber;
        GetComponent<Collider>().enabled = false;
        Utils.SetLayerRecursivelyByName(transform.gameObject, "Stacks");
    }

    // This function is temporal while I figure stacks out
    public void ObjDrop()
    {
        isGrabbed = false;
        grabber = null;
        isMoving = false;
        transform.gameObject.layer = LayerMask.NameToLayer("Default");
    }

    public void SetRandomModel()
    {
        if (models.Length > 0)
        {
            int randomIndex = Random.Range(0, models.Length);
            GameObject selectedModel = Instantiate(models[randomIndex], transform);
            selectedModel.transform.localPosition = Vector3.zero;
            selectedModel.layer = LayerMask.NameToLayer("Objects");
        }
    }

    private void LateUpdate()
    {
        if (isGrabbed && grabber != null && !isMoving)
        {
            transform.position = grabber.position + Vector3.up * (size + 1f);
        }
    }
}